# Changelog

# 1.0.0rc4
- fix 403 Error with no explanation (was streamlock related)
- readd support for streamlock
- concatenate all chunks of an episode in one lange `.ts` file

# 1.0.0rc3
- add single retry for chunk download

# 1.0.0rc2
- use csrf-token from meta fields not input since input is not always available

# 1.0.0rc1
- add verbose output option
- add `--no-keyring` option to login for system that have no keyring installed
- catch if no ffmpeg is installed

# 1.0.0rc0
- add more output
- better error formatting

# 0.6.0
- add quality selection
- save quality to config
- use the best quality available if max quality is not met
- get requirements from requirements.txt
- ensure Python version 3.8 or higher
- add config changing options
- refactor language/quality selection

## 0.5.0
- use click for progressbar
- save language preferences in config
- download multiple languages
- fix logout
- cleaned requirements