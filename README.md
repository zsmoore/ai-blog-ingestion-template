# AI Blog Ingestion Template
  
### What? A template for a worker to hit OpenAI + Google Image Search and ingest into Notion DB. Runs on Azure daily.
  
Use in partnership with [ai-blog-template](https://github.com/zsmoore/ai-blog-template) to serve the data.
  
### How to setup?

Create a .env file and add the following values
- `NOTION_TOKEN` - Notion API Key
- `DATABASE_ID` - Notion Database ID to push to
- `OPENAI_API_KEY` - Your OPENAI API Key
- `OPENAI_ORGANIZATION_ID` - Your OPENAI Organization Key
- `GCS_DEVELOPER_KEY` - Your Google search console api key
- `GCS_CX` - Key for google search engine
  
Hook up to Azure-Functions and it will be run daily at midnight UTC.

*PreReq* Sign up for notion. Get an API Key. Create a page which is a basic DB. Grab your key and DB id.  Sign up for an OPENAI API account.  Grab API Key and Organization ID.  Sign up for Google search console API. Get API Key. Create search engine in console. Get CTX key
  
Prompt Customization:  
Customize your prompt in the main.py files.  
Be careful not to change the prompt too much other than the content of the blog post being asked.  
The script looks for certain keywords in the open ai response.
  
Modify the default description in main.py  
  
*main.py* Duplicate of *TriggerIngestion/main.py* which prints to the screen rather than logs.  Use main.py for testing locally while TriggerIngestion/main.py will be run on azure.  
  
## Notion DB Format  
For your notion DB you need the following properties
- `Name` - title of blog post - rich text
- `Tags` - seo tags - multi select
- `Slug` - URL slug - rick text
- `Date` - Publish date - Date
- `Published` - Whether or not to show the blog - Checkbox
- `Description` - Description of blog post - rich text
- `Cover` - Cover image for post - File

Make sure to add the connection to your notion api settings for your db page.
