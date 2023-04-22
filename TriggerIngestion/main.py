import os
import json
import logging
from datetime import date

import openai
from dotenv import load_dotenv
from notion import NotionClient

OPENAI_API_KEY = 'OPENAI_API_KEY'
OPENAI_ORGANIZATION_ID = 'OPENAI_ORGANIZATION_ID'
NOTION_TOKEN = 'NOTION_TOKEN'
DATABASE_ID = 'DATABASE_ID'

MODEL = 'gpt-3.5-turbo'
WORD_COUNT = 3000
PROMPT = '''
Provide me a title for a blog post about something that happened on {0} in the past.
Then give me SEO tags for the blog post.
Then provide me an seo friendly url slug.
Then write me a blog post with over {1} words about the same event using professional language.
Do not include media.
Provide this information for me in json.
'''

DESCRIPTION = "On this day in history"

RETRY_COUNT = 5

CONTENT_NAMES = ['content', 'blog_post', 'post', 'Blog_post', 'blogPost']
SEO_TAG_NAMES = ['seo_tags', 'tags', 'SEO_tags', 'seoTags']
URL_SLUG_NAMES = ['url_slug', 'slug', 'URL_slug', 'seoFriendlySlug']
TITLE_NAMES = ['title', 'blog_post_title', 'Title', 'blogTitle']

CONTENT = 'content'
SEO_TAGS = 'seo_tags'
URL_SLUG = 'url_slug'
TITLE = 'title'


def initialize_openai(api_key, organization_id):
    openai.api_key = api_key
    openai.organization = organization_id


def initialize_client(notion_token):
    return NotionClient(auth=notion_token)


def ask_gpt(prompt):
    return openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {'role': 'user', 'content': prompt}
        ]
    )


def get_result_json(prompt):
    for i in range(0, RETRY_COUNT):
        resp = ask_gpt(prompt)
        result_json = try_parse_response(resp)
        if result_json:
            return result_json


def try_find_content(json, possible_names):
    for name in possible_names:
        if name in json:
            return json[name]
    return None


def try_parse_response(resp):
    try:
        content = resp['choices'][0]['message']['content']
        # Strip out chat gpt added messages
        if 'Note:' in content:
            content = content.split('Note:')[0]
        # Get a dictionary from the json
        content = json.JSONDecoder(strict=False).decode(content)

        blog_content = try_find_content(content, CONTENT_NAMES)
        tags = try_find_content(content, SEO_TAG_NAMES)
        slug = try_find_content(content, URL_SLUG_NAMES)
        title = try_find_content(content, TITLE_NAMES)
        should_throw = any(x is None for x in [blog_content, tags, slug, title])
        if should_throw:
            raise Exception('Couldn\'t find content')

        return {
            SEO_TAGS: tags,
            URL_SLUG: slug,
            TITLE: title,
            CONTENT: blog_content
        }
    except Exception as e:
        logging.error(e)
        logging.error('Failed to parse response')
        logging.error(resp)
        return None


def update_created_page_properties(notion_client, page_id, properties):
    return notion_client.pages.update(
        page_id=page_id,
        properties=properties)


def create_new_page(notion_client, database_id, content, children):
    return notion_client.pages.create(parent={
        'database_id': database_id
    }, properties=content, children=children)


def build_new_page_content(title):
    return {
        'Name': {
            'title': [
                {
                    'text': {
                        'content': title
                    }
                }
            ]
        }
    }


def chunk_content(content):
    logging.info('chunk triggered')
    split = [content[i: i + 1999] for i in range(0, len(content), 1999)]
    return map(lambda x: {
        'object': 'block',
        'type': 'paragraph',
        'paragraph': {
            'text': [
                {
                    'text': {
                        'content': x
                    }
                }
            ]
        }
    }, split)


def build_page_children(title, content):
    paragraphs = [
        {
            'object': 'block',
            'type': 'paragraph',
            'paragraph': {
                'text': [
                    {
                        'text': {
                            'content': content
                        }
                    }
                ]
            }
        }
    ]
    # notion limit
    if len(content) > 2000:
        paragraphs = chunk_content(content)

    return [
        {
            'object': 'block',
            'type': 'heading_1',
            'heading_1': {
                'text': [
                    {
                        'text': {
                            'content': title
                        }
                    }
                ]
            }
        },
        *paragraphs
    ]


def build_page_properties(tags, slug, date, description):
    tag_array = []
    for tag in tags:
        tag_array.append({
            'name': tag
        })
    return {
        'Slug': {
            'rich_text': [
                {
                    'text': {
                        'content': slug
                    }
                }
            ]
        },
        'Published': {
            'checkbox': True
        },
        'Description': {
            'rich_text': [
                {
                    'text': {
                        'content': description
                    }
                }
            ]
        },
        'Tags': {
            'multi_select': tag_array
        },
        'Date': {
            'date': {
                'start': date
            }
        }
    }


def main():
    logging.info('starting now')
    load_dotenv()
    openai_api_key = os.getenv(OPENAI_API_KEY)
    openai_organization_id = os.getenv(OPENAI_ORGANIZATION_ID)
    notion_token = os.getenv(NOTION_TOKEN)
    database_id = os.getenv(DATABASE_ID)

    initialize_openai(openai_api_key, openai_organization_id)
    prompt = PROMPT.format(date.today().strftime('%b %d'), WORD_COUNT)
    resp = get_result_json(prompt)
    if not resp:
        logging.info('no resp from openai')
        exit(1)
    else:
        logging.info('openai success')

    title = resp[TITLE]
    tags = resp[SEO_TAGS]
    slug = resp[URL_SLUG]
    content = resp[CONTENT]

    notion_client = initialize_client(notion_token)
    page_resp = create_new_page(notion_client, database_id, build_new_page_content(title),
                                build_page_children(title, content))
    page_id = page_resp.id
    logging.info('page created with ID {0}'.format(page_id))

    update_created_page_properties(notion_client, page_id, build_page_properties(tags, slug,
                                                                                 date.today().isoformat(),
                                                                                 DESCRIPTION))
    logging.info('page updated')
    logging.info('finished')


if __name__ == '__main__':
    main()
