use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::Path;

use crate::rules::md013::Md013Config;

#[derive(Debug, Deserialize, Serialize)]
pub struct MarkdownLintConfig {
    #[serde(default = "default_true")]
    pub default: bool,

    #[serde(rename = "MD013", default)]
    pub md013: Option<Md013ConfigWrapper>,

    #[serde(rename = "MD041", default)]
    pub md041: Option<bool>,

    #[serde(flatten)]
    pub other_rules: HashMap<String, serde_yaml::Value>,
}

fn default_true() -> bool {
    true
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(untagged)]
pub enum Md013ConfigWrapper {
    Enabled(bool),
    Config(Md013Config),
}

impl MarkdownLintConfig {
    pub fn from_file(path: &Path) -> Result<Self> {
        let content = fs::read_to_string(path)
            .with_context(|| format!("Failed to read config file: {}", path.display()))?;

        let config: Self = serde_yaml::from_str(&content)
            .with_context(|| format!("Failed to parse YAML from: {}", path.display()))?;

        Ok(config)
    }

    pub fn get_md013_config(&self) -> Option<Md013Config> {
        match &self.md013 {
            Some(Md013ConfigWrapper::Enabled(false)) => None,
            Some(Md013ConfigWrapper::Enabled(true)) => Some(Md013Config::default()),
            Some(Md013ConfigWrapper::Config(config)) => Some(config.clone()),
            None => {
                if self.default {
                    Some(Md013Config::default())
                } else {
                    None
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::NamedTempFile;

    #[test]
    fn test_parse_config() {
        let yaml = r#"
default: true

MD013:
  line_length: 100
  code_blocks: false
  tables: false

MD041: false
"#;

        let mut file = NamedTempFile::new().unwrap();
        write!(file, "{}", yaml).unwrap();

        let config = MarkdownLintConfig::from_file(file.path()).unwrap();

        assert!(config.default);
        let md013_config = config.get_md013_config().unwrap();
        assert_eq!(md013_config.line_length, 100);
        assert!(!md013_config.code_blocks);
        assert!(!md013_config.tables);
    }

    #[test]
    fn test_disabled_rule() {
        let yaml = r#"
default: true
MD013: false
"#;

        let mut file = NamedTempFile::new().unwrap();
        write!(file, "{}", yaml).unwrap();

        let config = MarkdownLintConfig::from_file(file.path()).unwrap();
        assert!(config.get_md013_config().is_none());
    }
}
