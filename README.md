# Archiver for Discord

This bot was designed to allow users to create a type of forum within discord using the new Modal interface. The idea was:
 - Users could create a thread:
   - Topic name
   - They specify a category (could be a school class, for example)
   - A description
   - Topic tags (csv)
 - The bot creates a channel in that category with the basic information and upvote and downvote buttons
 - Anyone with permissions could view that category and comment
 - Files, urls, edited comments would all be stored and updated
 - The original user could then archive that topic (i.e. close it)
 - Anyone could reopen it by searching for it using the search window
 - The reopened thread would:
   - Display the original information
   - Display any comments made by people (including their name, profile picture, time of being sent)
   - Contain links to files from the original thread
   - Create a json with all of the information
   - Create a styled HTML which could be downloaded and opened locally
   - Still be upvoted/downvoted for future reuses
 - Any text typed into inputs should be checked for similarity, not equality

# See screenshots folder for examples and UI
