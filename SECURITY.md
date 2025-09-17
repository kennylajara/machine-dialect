# Security Policy

## Supported Versions

Machine Dialect™ is currently in ALPHA stage. **Only the latest release receives security
updates and support.** Older releases are immediately deprecated when a new version is released.

### Python Versions

| Python Version | Supported          |
| -------------- | ------------------ |
| 3.13.x         | ✅                 |
| 3.12.x         | ✅                 |
| 3.11.x         | ✅                 |
| 3.10.x         | ✅                 |
| < 3.10         | ❌                 |

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
   - Use type hints for better safety
   - Run security linters
   - Keep dependencies updated

4. **Test security implications**
   - Consider security in your tests
   - Test error conditions
   - Verify access controls

## Dependency Management

- Dependencies are managed through UV and pyproject.toml
- Regular security audits are performed
- Known vulnerabilities are patched promptly

## Alpha Stage Notice

As Machine Dialect™ is in ALPHA:

- Breaking changes may occur for security improvements
- Security features are still being developed
- Not recommended for production use yet

## Contact

For security concerns, please contact the maintainers through:

- GitHub Security Advisories (preferred)
- Project maintainer: @kennylajara
