# Security Policy

## Supported Versions

Machine Dialect™ is currently in ALPHA stage. **Only the latest release receives security
updates and support.** Older releases are immediately deprecated when a new version is released.

### Runtime Versions

#### Python

| Python Version | Supported          |
| -------------- | ------------------ |
| 3.13.x         | ✅                 |
| 3.12.x         | ✅                 |
| 3.11.x         | ✅                 |
| 3.10.x         | ✅                 |
| < 3.10         | ❌                 |

#### Rust

| Rust Version   | Supported          |
| -------------- | ------------------ |
| Stable (latest)| ✅                 |
| Beta           | ⚠️ (best effort)   |
| Nightly        | ❌                 |

### Operating Systems

| Platform       | Supported          |
| -------------- | ------------------ |
| Ubuntu (latest)| ✅                 |
| Windows (latest)| ✅                |
| macOS (latest) | ✅                 |

## Reporting a Vulnerability

If you discover a security vulnerability in Machine Dialect™, please report it by:

1. **DO NOT** create a public GitHub issue
2. Create a private security advisory on GitHub

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Time

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Resolution Target**: Within 30 days for critical issues

## Security Best Practices

When contributing to Machine Dialect™:

1. **Never commit secrets or credentials**
   - API keys, passwords, tokens must never be in code
   - Use environment variables for sensitive data

2. **Validate all inputs**
   - Sanitize user inputs
   - Prevent injection attacks
   - Handle edge cases safely

3. **Follow secure coding guidelines**
   - Use type hints (Python) and strict typing (Rust)
   - Run security linters (ruff for Python, clippy for Rust)
   - Keep dependencies updated
   - No unsafe Rust code without thorough review

4. **Test security implications**
   - Consider security in your tests
   - Test error conditions
   - Verify access controls

## Dependency Management

### Python Dependencies

- Managed through UV and pyproject.toml
- Regular security audits via `pip audit`
- Known vulnerabilities are patched promptly

### Rust Dependencies

- Managed through Cargo.toml
- Regular audits via `cargo audit`
- Dependencies are kept minimal for security

## Alpha Stage Notice

As Machine Dialect™ is in ALPHA:

- Breaking changes may occur for security improvements
- Security features are still being developed
- Not recommended for production use yet

## Contact

For security concerns, please contact the maintainers through:

- GitHub Security Advisories (preferred)
- Project maintainer: @kennylajara
