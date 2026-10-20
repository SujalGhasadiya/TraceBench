import pytest
from backend.app.languages.detector import detect_language, is_ignored_path
from backend.app.languages.registry import get_supported_languages, get_capability
from backend.app.parsers.unified_parser import UnifiedParser
from backend.app.models.schemas import SymbolType

@pytest.fixture
def parser():
    return UnifiedParser()

def test_language_detection():
    assert detect_language("app.py") == "python"
    assert detect_language("index.js") == "javascript"
    assert detect_language("component.tsx") == "typescript"
    assert detect_language("Main.java") == "java"
    assert detect_language("main.c") == "c"
    assert detect_language("calc.cpp") == "cpp"
    assert detect_language("server.go") == "go"
    assert detect_language("lib.rs") == "rust"
    assert detect_language("index.php") == "php"
    assert detect_language("README.md") == "text"
    assert detect_language("config.json") == "text"
    assert detect_language("binary.exe") is None

def test_ignored_paths():
    assert is_ignored_path(".git/HEAD") is True
    assert is_ignored_path("node_modules/react/index.js") is True
    assert is_ignored_path("src/__pycache__/app.cpython-311.pyc") is True
    assert is_ignored_path(".env") is True
    assert is_ignored_path("secret_key.pem") is True
    assert is_ignored_path("id_rsa") is True
    assert is_ignored_path("src/utils.py") is False
    assert is_ignored_path("frontend/src/App.tsx") is False

def test_all_nine_languages_registered():
    langs = get_supported_languages()
    expected = ["python", "javascript", "typescript", "java", "c", "cpp", "go", "rust", "php"]
    for l in expected:
        assert l in langs
        cap = get_capability(l)
        assert cap.ast_supported is True
        assert cap.relationships_supported is True

def test_python_parsing(parser):
    code = """
def calculate_tax(amount: float) -> float:
    \"\"\"Calculates tax for income.\"\"\"
    return amount * 0.2

class OrderService:
    def process_order(self, order_id: str):
        return calculate_tax(100.0)
"""
    res = parser.parse_file("order.py", code, "repo1", "python")
    assert res.is_parsed is True
    names = {s.name: s for s in res.symbols}
    assert "calculate_tax" in names
    assert names["calculate_tax"].symbol_type == SymbolType.FUNCTION
    assert names["calculate_tax"].docstring == "Calculates tax for income."
    assert "OrderService" in names
    assert names["OrderService"].symbol_type == SymbolType.CLASS
    assert "OrderService.process_order" in names
    assert names["OrderService.process_order"].symbol_type == SymbolType.METHOD
    assert any(c["callee_name"] == "calculate_tax" for c in res.calls)

def test_javascript_parsing(parser):
    code = """
import { helper } from './utils';

function validateUser(user) {
    helper(user);
    return true;
}

class AuthManager {
    login(credentials) {
        return validateUser(credentials);
    }
}
"""
    res = parser.parse_file("auth.js", code, "repo1", "javascript")
    assert res.is_parsed is True
    names = {s.name: s for s in res.symbols}
    assert "validateUser" in names
    assert "AuthManager" in names
    assert len(res.imports) >= 1
    assert any("helper" in c["callee_name"] or "validateUser" in c["callee_name"] for c in res.calls)

def test_typescript_parsing(parser):
    code = """
interface UserProfile {
    id: string;
    username: string;
}

class UserService {
    getUser(id: string): UserProfile {
        return { id, username: 'test' };
    }
}
"""
    res = parser.parse_file("user.ts", code, "repo1", "typescript")
    assert res.is_parsed is True
    names = {s.name: s for s in res.symbols}
    assert "UserProfile" in names
    assert names["UserProfile"].symbol_type == SymbolType.INTERFACE
    assert "UserService" in names

def test_java_parsing(parser):
    code = """
package com.example;
import java.util.List;

public class PaymentProcessor {
    public void executePayment(double amount) {
        logTransaction(amount);
    }
}
"""
    res = parser.parse_file("PaymentProcessor.java", code, "repo1", "java")
    assert res.is_parsed is True
    names = {s.name: s for s in res.symbols}
    assert "PaymentProcessor" in names
    assert names["PaymentProcessor"].symbol_type == SymbolType.CLASS
    assert "PaymentProcessor.executePayment" in names
    assert len(res.imports) >= 1

def test_c_parsing(parser):
    code = """
#include <stdio.h>
struct Connection {
    int socket_fd;
};

int open_socket(int port) {
    printf("Opening port %d", port);
    return port;
}
"""
    res = parser.parse_file("net.c", code, "repo1", "c")
    assert res.is_parsed is True
    names = {s.name: s for s in res.symbols}
    assert "open_socket" in names
    assert "Connection" in names
    assert len(res.imports) >= 1

def test_cpp_parsing(parser):
    code = """
#include <vector>

class DatabaseConnection {
public:
    void connect() {
        initPool();
    }
};
"""
    res = parser.parse_file("db.cpp", code, "repo1", "cpp")
    assert res.is_parsed is True
    names = {s.name: s for s in res.symbols}
    assert "DatabaseConnection" in names
    assert "DatabaseConnection.connect" in names

def test_go_parsing(parser):
    code = """
package main

import "net/http"

type Router struct {
    port int
}

func (r *Router) ListenAndServe() {
    http.ListenAndServe(":8080", nil)
}
"""
    res = parser.parse_file("server.go", code, "repo1", "go")
    assert res.is_parsed is True
    names = {s.name: s for s in res.symbols}
    assert "Router" in names
    assert "Router.ListenAndServe" in names
    assert len(res.imports) >= 1

def test_rust_parsing(parser):
    code = """
use std::collections::HashMap;

struct Cache {
    items: HashMap<String, String>,
}

fn initialize_cache() -> Cache {
    Cache { items: HashMap::new() }
}
"""
    res = parser.parse_file("cache.rs", code, "repo1", "rust")
    assert res.is_parsed is True
    names = {s.name: s for s in res.symbols}
    assert "Cache" in names
    assert "initialize_cache" in names
    assert len(res.imports) >= 1

def test_php_parsing(parser):
    code = """
<?php
namespace App\\Controllers;

use App\\Models\\User;

class HomeController {
    public function showProfile($id) {
        $user = User::find($id);
        return $user;
    }
}
"""
    res = parser.parse_file("HomeController.php", code, "repo1", "php")
    assert res.is_parsed is True
    names = {s.name: s for s in res.symbols}
    assert "HomeController" in names
    assert "HomeController.showProfile" in names
    assert len(res.imports) >= 1

def test_text_fallback_parsing(parser):
    code = "# Project Documentation\nThis is a sample markdown file."
    res = parser.parse_file("README.md", code, "repo1", "text")
    assert res.is_parsed is False
    assert len(res.symbols) == 0
    assert len(res.errors) == 0
