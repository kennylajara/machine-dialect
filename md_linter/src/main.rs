mod config;
mod rules;

use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use std::path::{Path, PathBuf};

use crate::config::MarkdownLintConfig;
use crate::rules::md013::Md013Linter;

#[derive(Parser)]
#[command(name = "md_linter")]
#[command(about = "A Markdown linter with MD013 rule support", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Check markdown files for violations
    Check {
        /// Path to the markdown file(s) to check
        #[arg(value_name = "FILE")]
        files: Vec<PathBuf>,

        /// Path to the configuration file (default: .markdownlint.yaml)
        #[arg(short, long, default_value = ".markdownlint.yaml")]
        config: PathBuf,
    },

    /// Fix markdown files
    Fix {
        /// Path to the markdown file(s) to fix
        #[arg(value_name = "FILE")]
        files: Vec<PathBuf>,

        /// Path to the configuration file (default: .markdownlint.yaml)
        #[arg(short, long, default_value = ".markdownlint.yaml")]
        config: PathBuf,

        /// Dry run - show what would be fixed without writing changes
        #[arg(short, long)]
        dry_run: bool,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Check { files, config } => {
            check_files(&files, &config)?;
        }
        Commands::Fix { files, config, dry_run } => {
            fix_files(&files, &config, dry_run)?;
        }
    }

    Ok(())
}

fn check_files(files: &[PathBuf], config_path: &Path) -> Result<()> {
    let config = MarkdownLintConfig::from_file(config_path)
        .with_context(|| format!("Failed to load config from: {}", config_path.display()))?;

    let mut found_violations = false;

    if let Some(md013_config) = config.get_md013_config() {
        let linter = Md013Linter::new(md013_config);

        for file_path in files {
            let violations = linter.check_file(file_path)
                .with_context(|| format!("Failed to check file: {}", file_path.display()))?;

            if !violations.is_empty() {
                found_violations = true;
                print!("{}", linter.format_violations(&violations, file_path));
            }
        }
    }

    if found_violations {
        std::process::exit(1);
    }

    Ok(())
}

fn fix_files(files: &[PathBuf], config_path: &Path, dry_run: bool) -> Result<()> {
    let config = MarkdownLintConfig::from_file(config_path)
        .with_context(|| format!("Failed to load config from: {}", config_path.display()))?;

    if let Some(md013_config) = config.get_md013_config() {
        let linter = Md013Linter::new(md013_config);

        for file_path in files {
            let fixed_content = linter.fix_file(file_path)
                .with_context(|| format!("Failed to fix file: {}", file_path.display()))?;

            if dry_run {
                println!("=== {} (preview) ===", file_path.display());
                println!("{}", fixed_content);
                println!();
            } else {
                std::fs::write(file_path, &fixed_content)
                    .with_context(|| format!("Failed to write fixed content to: {}", file_path.display()))?;
                println!("Fixed: {}", file_path.display());
            }
        }
    }

    Ok(())
}
