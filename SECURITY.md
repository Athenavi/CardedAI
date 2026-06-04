# Security Policy

## 🔒 Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported             |
|---------|-----------------------|
| 0.x.x   | ✅ Active support      |
| < 0.x   | ❌ No longer supported |

## 🐛 Reporting a Vulnerability

We take the security of FastBlog seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to **[security@fastblog.dev](mailto:security@fastblog.dev)** (or the project
maintainer's email).

You should receive a response within **48 hours**. If for some reason you do not, please follow up to ensure we received
your original message.

### What to Include

Please include the following information in your report:

- Type of vulnerability (e.g., SQL injection, XSS, CSRF, etc.)
- Full paths of source file(s) related to the vulnerability
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### What to Expect

- **Acknowledgment** within 48 hours
- **Status update** within 7 days
- **Fix timeline** depending on severity:
    - 🔴 Critical: Within 24-48 hours
    - 🟠 High: Within 7 days
    - 🟡 Medium: Within 30 days
    - 🟢 Low: Next regular release

### Safe Harbor

We support responsible disclosure and will not take legal action against researchers who:

- Make a good faith effort to avoid privacy violations
- Only interact with accounts you own or with explicit permission
- Do not exploit a vulnerability beyond what is necessary to confirm its existence
- Do not publicly disclose the vulnerability until a fix is available

## 🛡️ Security Best Practices

When deploying FastBlog in production:

1. **Always use HTTPS** — Never run production without TLS
2. **Change default secrets** — Rotate all default keys and passwords
3. **Enable rate limiting** — Protect against brute force attacks
4. **Keep dependencies updated** — Regularly run `pip audit` and `npm audit`
5. **Use environment variables** — Never hardcode credentials
6. **Enable audit logging** — Monitor for suspicious activity
7. **Restrict CORS** — Only allow trusted origins
8. **Regular backups** — Maintain automated backup schedule

## 🔐 Security Features

FastBlog includes the following security features:

- JWT-based authentication with refresh tokens
- Two-factor authentication (TOTP)
- CSRF protection
- SQL injection prevention (ORM-based queries)
- XSS protection (output sanitization)
- Rate limiting (configurable per endpoint)
- Password hashing (bcrypt)
- Role-based access control (RBAC)
- Audit logging for sensitive operations

## 📋 Security Checklist for Deployment

- [ ] Changed all default passwords and secret keys
- [ ] Set `DEBUG=False` in production
- [ ] Configured HTTPS with valid certificates
- [ ] Set up proper CORS allowed origins
- [ ] Enabled rate limiting
- [ ] Configured proper database access controls
- [ ] Set up monitoring and alerting
- [ ] Enabled audit logging
- [ ] Configured automated backups
- [ ] Updated all dependencies to latest versions
