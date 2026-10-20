package main

import (
	"fmt"
	"net/http"
)

type Router struct {
	Port int
}

func (r *Router) ListenAndServe() {
	addr := fmt.Sprintf(":%d", r.Port)
	fmt.Printf("Starting HTTP server on %s\n", addr)
	http.HandleFunc("/health", func(w http.ResponseWriter, req *http.Request) {
		w.Write([]byte("OK"))
	})
	http.ListenAndServe(addr, nil)
}
