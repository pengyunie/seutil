# v1.0 Planned Features and Changes

- `IOUtils`

  - Combine `load` with `jsonfy`, combine `dump` with `dejsonfy`
  
  - Support `jsonfy` numpy numbers directly
  
  - Add `loadl` and `dumpl` for jsonList and txtList format, which
    support showing progress bar
    
- `CliUtils`

  - Option without values should not default to `1`, but default to
    `True` or user specified value
    
  - Support parsing lists separated by whitespace or user specified
    char (`,`, `;`)
    
  - Support parsing dicts in json/yaml format
  
- `GitHubUtils`

  - Change `search_repos_of_language` with a better strategy
  
- `project`

  - Remove "results"
  
  - Add `ProjectManager` to manage the downloads_dir
  
- config

  - Add UI to add/modify/remove user specific configs (e.g., GitHub
    access token)
    
- `LoggingUtils`

  - Change to something like a `LogManager` to use instance level
    configs
    
- latex

  - Add some util functions: `escape_str` etc
  
  - Make `File.__init__` accept additional parameter `owner: str`
  
  - Add `Table` class

- Interaction with JVM

- @deprecated annotation
