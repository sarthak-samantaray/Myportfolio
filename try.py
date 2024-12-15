from flask import Flask, render_template
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import re
from datetime import datetime

app = Flask(__name__)
# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/blogs"
mongo_blogs = PyMongo(app)

try:
    mongo = PyMongo(app)
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    mongo = None  # Ensure mongo is None if connection fails

def parse_markdown(content):
        # Define patterns for each Markdown element
    patterns = {
        "heading_1": r"^#\s+(.*)$",          # Matches Heading 1 (# Heading)
        "heading_2": r"^##\s+(.*)$",         # Matches Heading 2 (## Heading)
        "heading_3": r"^###\s+(.*)$",        # Matches Heading 3 (### Heading)
        "heading_4": r"^####\s+(.*)$",       # Matches Heading 4 (#### Heading)
        "code_block": r"```([\s\S]*?)```",   # Matches code blocks
        "image": r"!\[.*?\]\((.*?)\)",       # Matches Markdown images
        "text": r"^[^#!\n`][^\n]*$"          # Matches normal text
    }
    
    # Priority order to parse content
    priority = ["heading_1", "heading_2", "heading_3", "heading_4", "code_block", "image", "text"]
    
    # Initialize results list
    results = []
    
    # Split content into lines while preserving code blocks
    lines = content.strip().split('\n')
    
    # Process content line by line
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
            
        # Handle code blocks first
        if line.startswith('```'):
            code_content = []
            i += 1  # Skip the opening ```
            while i < len(lines) and not lines[i].strip().endswith('```'):
                code_content.append(lines[i])
                i += 1
            if i < len(lines):  # Add the last line without the closing ```
                code_content.append(lines[i].strip().rstrip('`'))
            results.append({
                'type': 'code_block',
                'content': '\n'.join(code_content)
            })
            i += 1
            continue
            
        # Check for headings
        for heading_type in ["heading_1", "heading_2", "heading_3", "heading_4"]:
            match = re.match(patterns[heading_type], line)
            if match:
                heading_content = match.group(1).strip()  
                results.append({
                    'type': heading_type,
                    'content': heading_content
                })
                break
        else:
            # Check for images
            image_match = re.search(patterns["image"], line)
            if image_match:
                results.append({
                    'type': 'image',
                    'content': image_match.group(1)
                })
            # Check for regular text
            elif re.match(patterns["text"], line):
                results.append({
                    'type': 'text',
                    'content': line
                })
        i += 1
    
    return results

@app.route('/')
def index():
        # Ensure MongoDB is connected
        if mongo is None:
            return "Database connection error", 500

        # Fetch a single blog by ID
        blog_post = mongo_blogs.db.blogs_lists.find_one({"_id": ObjectId('675ea5ec9948dbf1ca5251ab')})
        print(blog_post)
        # Check if the blog exists
        if not blog_post:
            return "Blog not found", 404

        # Now try to fetch the specific blog
        if blog_post:
            # Parse the markdown content
            print(blog_post['content'])
            parsed_content = parse_markdown(blog_post['content'])
            print("Parsed_Content",parsed_content)
            # Format the date
            formatted_date = blog_post['edit_date'].strftime('%B %d, %Y') if isinstance(blog_post['edit_date'], datetime) else blog_post['edit_date']

            return render_template('delete_this.html', 
                                post=blog_post,
                                content=parsed_content,
                                formatted_date=formatted_date)
        else:
            all_ids = [str(post['_id']) for post in mongo_blogs.db.blogs_lists.find({}, {'_id': 1})]
            return f"Blog post with ID '675e76aa2f1568af4d8a10c2' not found. Available blog IDs: {all_ids}", 404

if __name__ == '__main__':
    app.run(debug=True)