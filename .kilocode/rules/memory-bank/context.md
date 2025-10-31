# Current Context

## Work Focus
Year-based order extraction functionality is fully implemented and ready for testing.

## Recent Changes
- Removed --max-orders argument from command line interface
- Added --start-year and --end-year arguments for year-based filtering
- Updated configuration system to support year ranges instead of order limits
- Modified browser controller to navigate to year-specific Amazon URLs
- Implemented year-based extraction logic in data extractor
- Updated main application flow to handle year ranges
- Tested changes successfully - application compiles and help shows new options

## Next Steps
- Test end-to-end functionality with actual Amazon pages
- Consider adding validation for year ranges (reasonable bounds)
- Update README.md with new command line options
- Add unit tests for year-based extraction logic