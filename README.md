# ExtraBackup

> **ExtraBackup --- Give your backups a warm (or multiple) home**\
> A distributed backup plugin for MCDR that automatically uploads your
> world backups to another hard drive, NAS, or even cloud services like
> Baidu Netdisk (planned).\
> Prevents data loss in case your server drive suddenly dies :P

Current version only supports **local disk backup**. FTP and other modes
are under development.

------------------------------------------------------------------------

## 📦 Features

-   Automatically uploads backups exported by PrimeBackup
-   Supports multiple backup destinations (distributed backup)
-   Automatically skips duplicate files
-   Supports download / delete / prune operations
-   Supports multilingual UI
-   Supports simple interval-based scheduled backup & prune tasks

------------------------------------------------------------------------

## 🧭 Command Guide

### `!!exb upload <id> [tag]`

Upload a specific backup from the PB export folder (usually
`pb_files/export`).
- Supports special PB IDs like `latest`, `~3`, etc.
- `tag` is optional.

------------------------------------------------------------------------

### `!!exb uploadall`

Upload **all** backups in the export folder.\
Automatically skips duplicate files.

------------------------------------------------------------------------

### `!!exb download <file_name> [from]`

Download a backup file from a specified backup path.
- `file_name`: name of the backup file
- `from`: backup path name (optional).
- If omitted, the plugin will choose a random available backup path.

------------------------------------------------------------------------

### `!!exb list [location]`

List all files from a backup path.
- If `location` is omitted → lists local backup files.

------------------------------------------------------------------------

### `!!exb prune [id]`

Clean outdated files.
- If an `id` is given → prune that file specifically
- If omitted → prune all outdated files
- Outdated time is configured in `config.json`

------------------------------------------------------------------------

### `!!exb delete <file_name> <location>`

Delete a specific backup from a specific backup path.

------------------------------------------------------------------------

### `!!exb lang <language>`

Switch plugin language.\
Supported languages:

-   `zh_cn` --- Chinese
-   `en_us` --- English

------------------------------------------------------------------------

## ⚙️ Configuration Guide

### Main Config --- `config.json`

``` jsonc
{
    "enable": "false",            // Whether to enable the plugin
    "language": "zh_cn",          // Default language
    "max_thread": "-1",           // Max upload/download threads (-1 = no limit)

    "schedule_backup": {
        "enable": "false",        // Enable scheduled backup
        "interval": "30m"         // Upload interval
    },

    "schedule_prune": {
        "enable": "false",        // Enable scheduled prune
        "interval": "1d",         // Prune interval
        "max_lifetime": "3d",     // Maximum file lifetime

        "prune_downloads": "true", // Whether to clean exb_downloads folder
        "prune_exports": "true"    // Whether to clean PB export folder
    }
}
```

------------------------------------------------------------------------

## 📁 Backup Path Config ---
`backup_path.json` 

``` jsonc
{
    "Name1": {                          // Backup path name (supports Chinese)
        "enable": "false",              // Whether this backup path is enabled
        "mode": "ftp",                  // "local" = local path; "ftp" = remote FTP server
        "address": "ftp://example.com/folder", // For local: use local path; for FTP: server URL
        "username": "username",         // FTP username; leave empty for local mode
        "password": "123456"            // FTP password; leave empty for local mode
    },

    "Name2": {
        "enable": "true",
        "mode": "local",
        "address": "/folder/example",   // Local backup directory path
        "username": "",                 // Must remain empty string in local mode
        "password": ""                  // Must remain empty string in local mode
    }
}
```

------------------------------------------------------------------------

