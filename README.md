# envault

> Encrypt and manage `.env` files with team-sharing support via S3 or local backends.

---

## Installation

```bash
pip install envault
```

Or with optional S3 support:

```bash
pip install envault[s3]
```

---

## Usage

**Initialize a vault in your project:**

```bash
envault init
```

**Encrypt and store your `.env` file:**

```bash
envault push .env
```

**Pull and decrypt a shared `.env` file:**

```bash
envault pull .env
```

**Use an S3 backend for team sharing:**

```bash
envault init --backend s3 --bucket my-team-bucket
envault push .env
```

**Rotate encryption keys:**

```bash
envault rotate
```

Configuration is stored in `.envault.yml`. Add your vault key to your password manager or CI secrets — never commit it.

---

## Backends

| Backend | Description |
|---------|-------------|
| `local` | Stores encrypted vault on disk (default) |
| `s3` | Stores encrypted vault in an AWS S3 bucket |

---

## License

MIT © [envault contributors](https://github.com/yourname/envault)