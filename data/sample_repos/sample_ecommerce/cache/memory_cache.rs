use std::collections::HashMap;

pub struct Cache {
    storage: HashMap<String, String>,
}

pub fn initialize_cache() -> Cache {
    Cache {
        storage: HashMap::new(),
    }
}

impl Cache {
    pub fn get(&self, key: &str) -> Option<&String> {
        self.storage.get(key)
    }

    pub fn set(&mut self, key: String, val: String) {
        self.storage.insert(key, val);
    }
}
