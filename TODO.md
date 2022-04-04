# v1.0 Planned Features and Changes

- CliUtils -> use jsonargparse instead
    
- latex

  - When generating new \UseMacro in tables (e.g., table caption and
    name), if that macro is not \DefMacro'd in macros.tex,
    automatically add that.

  - Add some util functions: `escape_str` etc
  
  - Make `File.__init__` accept additional parameter `owner: str`
  
  - Add `Table` class:
    specify columns -> generate \begin{tabular}{...}
    support separators (\midrule), multirow, multicolumn, spaces between columns/rows

- IOUtils -> io

  + Rename API rm_dir > rmdir
  + Re-add API mkdir
  
  + More powerful and easy-to-use load & dump functions
    + support serialization (replacing the original jsonfy & dejsonfy)
    + support xList formats together with others, and optional progress bar for them
    
  - Serialization: support numpy array and pd.DataFrame
    
- debug

  ~ Function to print debugging information any object with varying verbosity:
    name, type, size, string representation
    
  ~ Function to shrink a complex data structure to a small size for debugging
  
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

- Interaction with JVM

- @deprecated annotation
