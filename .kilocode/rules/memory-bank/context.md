# Current Context

## Work Focus
Year-based order extraction functionality is fully implemented and tested. Caching system for debugging and re-processing is now available.

## Recent Changes
- Removed --max-orders argument from command line interface
- Added --start-year and --end-year arguments for year-based filtering
- Updated configuration system to support year ranges instead of order limits
- Modified browser controller to navigate to year-specific Amazon URLs
- Implemented year-based extraction logic in data extractor
- Updated main application flow to handle year ranges
- Added comprehensive caching system (CacheManager) for debugging and re-processing
- Implemented cache loading/saving functionality with --use-cache and --save-cache options
- Added --list-cache option to view available cached data
- Tested changes successfully - application compiles and all new options work correctly

## Next Steps
- Test end-to-end functionality with actual Amazon pages
- Consider adding validation for year ranges (reasonable bounds)
- Update README.md with new command line options (caching features)
- Add unit tests for year-based extraction logic and cache manager
- Consider adding cache compression for large datasets