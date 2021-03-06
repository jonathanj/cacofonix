# Changelog

Cacofonix issues are filed on [GitHub](https://github.com/jonathan/cacofonix/issues), and each ticket number here corresponds to a closed GitHub issue.

<!-- Generated release notes start. -->

## [0.1.6] - 2021-01-22

### Fixed

- Fix `render_fragment` code broken by upstream Towncrier changes.


## [0.1.5] - 2020-05-28

### Fixed

- Crash occurs when the `next` fragment directory doesn't exist. [#10](https://github.com/jonathanj/cacofonix/issues/10)
- Change fragments with non-string keys cause a crash in Towncrier. [#9](https://github.com/jonathanj/cacofonix/issues/9)


## [0.1.3] - 2020-02-04

### Fixed

- Exception trying to detect software versions in package.json files. [#7](https://github.com/jonathanj/cacofonix/issues/7)


## [0.1.2] - 2020-02-04

### Added

- Fragments are now archived instead of deleted. [#5](https://github.com/jonathanj/cacofonix/issues/5)
  - The version number is used as the directory name with `next` being used for the as-yet-unreleased version.


## 0.1.1 (2020-01-31)

### Added

- Interactive mode is now significantly enhanced: [#3](https://github.com/jonathanj/cacofonix/issues/3)
    - Colored prompts;
    - Autocompleting prompts for change types and sections;
    - Syntax-highlighted, multiline (with readline-like support), description prompt;
    - Preview of the YAML to be generated.


