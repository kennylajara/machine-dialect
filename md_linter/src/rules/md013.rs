use anyhow::Result;
use regex::Regex;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;
use textwrap::{fill, Options};

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct Md013Config {
    pub line_length: usize,
    #[serde(default)]
    pub code_blocks: bool,
    #[serde(default)]
    pub tables: bool,
}

impl Default for Md013Config {
    fn default() -> Self {
        Self {
            line_length: 80,
            code_blocks: true,
            tables: true,
        }
    }
}

#[derive(Debug, Clone)]
pub struct Violation {
    pub line_number: usize,
    pub actual_length: usize,
    pub expected_length: usize,
    #[allow(dead_code)]
    pub line_content: String,
}

pub struct Md013Linter {
    config: Md013Config,
    code_block_regex: Regex,
    table_regex: Regex,
}

impl Md013Linter {
    pub fn new(config: Md013Config) -> Self {
        Self {
            config,
            code_block_regex: Regex::new(r"^```").unwrap(),
            table_regex: Regex::new(r"^\|.*\|").unwrap(),
        }
    }

    pub fn check_file(&self, file_path: &Path) -> Result<Vec<Violation>> {
        let content = fs::read_to_string(file_path)?;
        let violations = self.check_content(&content);
        Ok(violations)
    }

    pub fn check_content(&self, content: &str) -> Vec<Violation> {
        let mut violations = Vec::new();
        let mut in_code_block = false;

        for (line_number, line) in content.lines().enumerate() {
            // Toggle code block state
            if self.code_block_regex.is_match(line) {
                in_code_block = !in_code_block;
                continue;
            }

            // Skip if in code block and code_blocks is false
            if in_code_block && !self.config.code_blocks {
                continue;
            }

            // Skip if table line and tables is false
            if self.table_regex.is_match(line) && !self.config.tables {
                continue;
            }

            let line_length = line.chars().count();
            if line_length > self.config.line_length {
                violations.push(Violation {
                    line_number: line_number + 1,
                    actual_length: line_length,
                    expected_length: self.config.line_length,
                    line_content: line.to_string(),
                });
            }
        }

        violations
    }

    pub fn fix_file(&self, file_path: &Path) -> Result<String> {
        let content = fs::read_to_string(file_path)?;
        let fixed_content = self.fix_content(&content);
        Ok(fixed_content)
    }

    pub fn fix_content(&self, content: &str) -> String {
        let mut result = Vec::new();
        let mut in_code_block = false;

        let wrap_options = Options::new(self.config.line_length)
            .break_words(false)
            .word_separator(textwrap::WordSeparator::AsciiSpace);

        for line in content.lines() {
            // Toggle code block state
            if self.code_block_regex.is_match(line) {
                in_code_block = !in_code_block;
                result.push(line.to_string());
                continue;
            }

            // Don't wrap if in code block and code_blocks is false
            if in_code_block && !self.config.code_blocks {
                result.push(line.to_string());
                continue;
            }

            // Don't wrap if table line and tables is false
            if self.table_regex.is_match(line) && !self.config.tables {
                result.push(line.to_string());
                continue;
            }

            // Check if line is too long
            if line.chars().count() > self.config.line_length {
                // Handle different line types
                if line.trim_start().starts_with("- ") || line.trim_start().starts_with("* ") {
                    // List item - preserve indentation and marker
                    let indent = line.len() - line.trim_start().len();
                    let indent_str = &line[..indent];
                    let marker_end = line.find(' ').unwrap_or(line.len());
                    let marker = &line[indent..=marker_end];
                    let content = &line[marker_end + 1..];

                    let wrapped = fill(content, &wrap_options);
                    let lines: Vec<&str> = wrapped.lines().collect();

                    // First line with marker
                    result.push(format!("{}{}{}", indent_str, marker, lines[0]));

                    // Continuation lines with extra indent
                    for continuation in &lines[1..] {
                        result.push(format!("{}  {}", indent_str, continuation));
                    }
                } else if line.trim_start().starts_with(|c: char| c.is_numeric())
                    && line.contains(". ")
                {
                    // Numbered list - similar handling
                    let indent = line.len() - line.trim_start().len();
                    let indent_str = &line[..indent];
                    let marker_end = line.find(". ").unwrap() + 2;
                    let marker = &line[indent..marker_end];
                    let content = &line[marker_end..];

                    let wrapped = fill(content, &wrap_options);
                    let lines: Vec<&str> = wrapped.lines().collect();

                    result.push(format!("{}{}{}", indent_str, marker, lines[0]));

                    for continuation in &lines[1..] {
                        result.push(format!("{}   {}", indent_str, continuation));
                    }
                } else if line.trim_start().starts_with("#") {
                    // Headers - don't wrap
                    result.push(line.to_string());
                } else if line.trim().is_empty() {
                    // Empty lines
                    result.push(line.to_string());
                } else {
                    // Regular paragraph text
                    let wrapped = fill(line, &wrap_options);
                    for wrapped_line in wrapped.lines() {
                        result.push(wrapped_line.to_string());
                    }
                }
            } else {
                result.push(line.to_string());
            }
        }

        result.join("\n")
    }

    pub fn format_violations(&self, violations: &[Violation], file_path: &Path) -> String {
        let mut output = String::new();

        for violation in violations {
            output.push_str(&format!(
                "{}:{} MD013/line-length Line length [Expected: {}; Actual: {}]\n",
                file_path.display(),
                violation.line_number,
                violation.expected_length,
                violation.actual_length
            ));
        }

        output
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_line_length_detection() {
        let config = Md013Config {
            line_length: 20,
            code_blocks: false,
            tables: false,
        };
        let linter = Md013Linter::new(config);

        let content = "This is a short line\nThis is a very long line that exceeds the limit";
        let violations = linter.check_content(content);

        assert_eq!(violations.len(), 1);
        assert_eq!(violations[0].line_number, 2);
    }

    #[test]
    fn test_code_block_skipping() {
        let config = Md013Config {
            line_length: 20,
            code_blocks: false,
            tables: false,
        };
        let linter = Md013Linter::new(config);

        let content =
            "Short line\n```\nThis is a very long line in a code block\n```\nAnother short line";
        let violations = linter.check_content(content);

        assert_eq!(violations.len(), 0);
    }

    #[test]
    fn test_line_wrapping() {
        let config = Md013Config {
            line_length: 20,
            code_blocks: false,
            tables: false,
        };
        let linter = Md013Linter::new(config);

        let content = "This is a very long line that needs to be wrapped properly";
        let fixed = linter.fix_content(content);

        for line in fixed.lines() {
            assert!(line.chars().count() <= 20);
        }
    }
}
