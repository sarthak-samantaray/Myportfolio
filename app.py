from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from bson import json_util
from flask import request
import json
from datetime import datetime
from flask import abort


app = Flask(__name__)

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/blogs"
mongo_blogs = PyMongo(app)

app.config["MONGO_URI"] = "mongodb://localhost:27017/projects"
mongo_projects = PyMongo(app)

app.config["MONGO_URI"] = "mongodb://localhost:27017/skills"
mongo_skills = PyMongo(app)

app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Directory to save uploaded files
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit upload size to 16 MB


try:
    mongo = PyMongo(app)
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    mongo = None  # Ensure mongo is None if connection fails

# Home Route
@app.route("/")
def home():
    try:
        blogs = mongo_blogs.db.blogs_lists.find()
        projects = mongo_projects.db.projects_lists.find({'show_on_main': True})  # Filter projects
        skills = mongo_skills.db.skills_details.find()
        print(skills)  # Fetch skills from the skills_details collection

    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return "Database connection error", 500  # Handle connection error

    return render_template("index.html", blogs=blogs, projects=projects , skill = skills)

# Blog Listing Page
@app.route("/blog")
def blog():
    if mongo is None:
        return "Database connection error", 500  # Handle connection error
    blogs = mongo_blogs.db.blogs_lists.find()
    blogs_list = list(blogs)

    # Get all unique tags for the filter dropdown
    tags = mongo_blogs.db.blogs_lists.distinct('tags')
    return render_template("blog.html", blogs=blogs_list , tags = tags)

# Blog Detail Page
import markdown
from markupsafe import Markup
@app.route("/blog/<blog_id>")
def blog_detail(blog_id):
        # Ensure MongoDB is connected
        if mongo is None:
            return "Database connection error", 500

        # Fetch a single blog by ID
        blog_post = mongo_blogs.db.blogs_lists.find_one({"_id": ObjectId(blog_id)})
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

            return render_template('blog_detail.html', 
                                post=blog_post,
                                content=parsed_content,
                                formatted_date=formatted_date)
        else:
            all_ids = [str(post['_id']) for post in mongo_blogs.db.blogs_lists.find({}, {'_id': 1})]
            return f"Blog post with ID '675e76aa2f1568af4d8a10c2' not found. Available blog IDs: {all_ids}", 404



@app.route('/filter_projects')
def fiter_projects():
    try:
        # Get filter parameters

        tags = request.args.get('tags')  # Get tags as a comma-separated string
        tag_list = tags.split(',') if tags else []

        # Create a query based on filters
        query = {}
        if tag_list:
            query['tags'] = {'$in': tag_list}  # Match blogs with any of the selected tags

        # Fetch filtered blogs from the database
        projects = list(mongo_projects.db.projects_lists.find(query))

        # Get all unique tags for the filter dropdown
        tags = mongo_projects.db.projects_lists.distinct('tags')
        # Render the filtered blogs to the UI
        return render_template('portfolio.html', projects=projects, tags=tags)

    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/portfolio')
def portfolio():
    if mongo is None:
        return "Database connection error", 500  # Handle connection error
    projects = mongo_projects.db.projects_lists.find()
    projects = list(projects)

    # Get all unique tags for the filter dropdown
    tags = mongo_projects.db.projects_lists.distinct('tags')
    return render_template("portfolio.html", projects=projects , tags = tags)
    

@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/about') 
def about():
    skills = mongo_skills.db.skills_details.find()
    return render_template('about.html',skills=skills) 

@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/save_updated_blog/<blog_id>")
def sae_updated_blog(blog_id):
    try:
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        tags = request.form.get('tags').split(',')
        tags = [tag.strip() for tag in tags]  # Clean up whitespace
        reading_time = request.form.get('reading_time')
        content = request.form.get('content')
        edit_date = request.form.get('edit_date')

        # Handle thumbnail update
        if 'thumbnail' in request.files and request.files['thumbnail'].filename != '':
            thumbnail = request.files['thumbnail']
            thumbnail_filename = secure_filename(thumbnail.filename)
            thumbnail.save(os.path.join('static/uploads', thumbnail_filename))
        else:
            thumbnail_filename = request.form.get('current_thumbnail')

        # Update document in MongoDB
        update_data = {
            "title": title,
            "description": description,
            "tags": tags,
            "reading_time": reading_time,
            "content": content,
            "edit_date": edit_date,
            "thumbnail": thumbnail_filename
        }

        mongo_blogs.db.blogs_lists.update_one(
            {"_id": ObjectId(blog_id)},
            {"$set": update_data}
        )

        return redirect(url_for('edit_blogs'))

    except Exception as e:
        print(f"Error updating blog: {e}")




# Utility function to fetch a blog by ID
def get_blog_by_id(blog_id):
    try:
        blog = mongo_blogs.db.blogs_lists.find_one({"_id": ObjectId(blog_id)})  # Ensure ObjectId is used
    except Exception:
        abort(404)  # Return 404 if the ID is invalid
    if blog is None:
        abort(404)  # Return 404 if the blog is not found
    return blog

@app.route("/update_blog/<blog_id>", methods=["GET", "POST"])
def update_blog(blog_id):
    blog = get_blog_by_id(blog_id)  # Retrieve the blog post
    if request.method == "POST":
        # Handle the form submission
        updated_data = {
            "title": request.form["title"],
            "description": request.form["description"],
            "tags": request.form["tags"].split(","),
            "content": request.form["content"],
            "reading_time": int(request.form["reading_time"]),
            "edit_date": request.form["edit_date"],
        }

        # Handle the thumbnail update
        if "thumbnail" in request.files:
            thumbnail = request.files["thumbnail"]
            if thumbnail.filename:  # Only update if a new file is uploaded
                thumbnail.save(f"static/uploads/{thumbnail.filename}")
                updated_data["thumbnail"] = thumbnail.filename
            else:
                updated_data["thumbnail"] = request.form["current_thumbnail"]

        mongo_blogs.db.blogs_lists.update_one({"_id": ObjectId(blog_id)}, {"$set": updated_data})
        return redirect(url_for("edit_blogs"))
    return render_template("update_blog.html", blog=blog)

@app.route('/edit_blogs')
def edit_blogs():
    if mongo is None:
        return "Database connection error", 500  # Handle connection error
    blogs = mongo_blogs.db.blogs_lists.find()  # Corrected `mongo_blogs`
    blogs_list = list(blogs)

    # Get all unique tags for the filter dropdown
    tags = mongo_blogs.db.blogs_lists.distinct('tags')  # Corrected `mongo_blogs`
    return render_template("edit_blogs.html", blogs=blogs_list, tags=tags)



################################## BLOG OPERATIONS ####################################


# Delete Blog Route
@app.route("/delete/<blog_id>", methods=["POST"])
def delete_blog(blog_id):
    if mongo is None:
        return "Database connection error", 500  # Handle connection error
    mongo_blogs.db.blogs_lists.delete_one({"_id": ObjectId(blog_id)})
    return redirect(url_for("edit_blogs"))

################################# Project Operation #########################################
@app.route("/add_projects", methods=["GET", "POST"])
def add_projects():
    if request.method == "POST":
        project_name = request.form.get("project_name")
        description = request.form.get("description")
        image = request.form.get("icon")
        link = request.form.get("link")
        show_on_main = 'show_on_main' in request.form
        tags = request.form.get("tags")
        
        # Handle file upload for the skill icon
        if 'icon' not in request.files:
            return "No file part", 400
        file = request.files['icon']
        if file.filename == '':
            return "No selected file", 400
        
        # Secure the filename and save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Create the URL for the uploaded icon
        icon_url = url_for('static', filename='uploads/' + filename)

        # Create a new skill entry
        new_project = {
            "title": project_name,
            "description": description,
            "link": link,
            "image_url" : icon_url,
            "show_on_main" : show_on_main,
            "tags" : tags
        }
        
        mongo_projects.db.projects_lists.insert_one(new_project)
        return redirect("/")  # Redirect to the about page or wherever you want

    return render_template("add_projects.html") 

################################## Skill OPERATIONS ####################################

@app.route("/add_skills", methods=["GET", "POST"])
def add_skills():
    if request.method == "POST":
        skill_name = request.form.get("skill_name")
        percentage = request.form.get("percentage")
        
        # Handle file upload for the skill icon
        if 'icon' not in request.files:
            return "No file part", 400
        file = request.files['icon']
        if file.filename == '':
            return "No selected file", 400
        
        # Secure the filename and save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Create the URL for the uploaded icon
        icon_url = url_for('static', filename='images/skill_logos/' + filename)

        # Create a new skill entry
        new_skill = {
            "name": skill_name,
            "icon_url": icon_url,
            "percentage": percentage
        }
        
        mongo_skills.db.skills_details.insert_one(new_skill)
        return redirect(url_for("about"))  # Redirect to the about page or wherever you want

    return render_template("add_skills.html")  # Create a template for adding skills




########################################### BLOG OPERATION #####################################
import json
# Add Blog Page
# Ensure the upload folder exists
import os
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
import re

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


@app.route("/add", methods=["GET", "POST"])
def add_blog():
    return render_template("add_blog.html")


@app.route('/upload', methods=['POST'])
def upload():
    if 'image' in request.files:
        image = request.files['image']
        if image.filename != '':
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
            image.save(filepath)
            return {'url': url_for('static', filename=f'uploads/{image.filename}')}, 200
    return {'error': 'No image uploaded'}, 400

from flask import jsonify
from flask import request, jsonify
import os
from bson import ObjectId
from werkzeug.utils import secure_filename

@app.route('/save', methods=['POST'])
def save():
    try:
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        tags = request.form.get('tags')  # Get tags as a comma-separated string
        edit_time = request.form.get('edit_time')
        reading_time = request.form.get('reading_time')
        content = request.form.get('content')

        # If tags are provided, split by comma
        if tags:
            tags = tags.split(',')  # Convert tags into a list
        else:
            tags = []

        # Get file data
        thumbnail = request.files.get('thumbnail')
        if thumbnail:
            thumbnail_filename = secure_filename(thumbnail.filename)
            thumbnail.save(os.path.join('static/uploads', thumbnail_filename))

        # Handle the rest of the data (tags, content, etc.)
        parsed_content = {
            "title": title,
            "description": description,
            "tags": tags,  # Save the tags list
            "edit_date": edit_time,
            "reading_time": reading_time,
            "content": content,
            "thumbnail": thumbnail_filename if thumbnail else None
        }

        # Save the blog data to MongoDB
        result = mongo_blogs.db.blogs_lists.insert_one(parsed_content)

        
        # Return response with the result
        return redirect(url_for('blog'))         

    except Exception as e:
        # Handle any unexpected errors
        return jsonify({'message': f'Error: {str(e)}'}), 500
    

@app.route('/filter', methods=['GET'])
def filter_blogs():
    try:
        # Get filter parameters
        month = request.args.get('month')
        year = request.args.get('year')
        tags = request.args.get('tags')  # Get tags as a comma-separated string
        tag_list = tags.split(',') if tags else []

        # Create a query based on filters
        query = {}
        if year:
            query['edit_date'] = {'$regex': f'^{year}'}  # Year at the start
        if month:
            query['edit_date'] = {'$regex': f'-{month}-'}  # Match specific month
        if tag_list:
            query['tags'] = {'$in': tag_list}  # Match blogs with any of the selected tags

        # Fetch filtered blogs from the database
        blogs = list(mongo_blogs.db.blogs_lists.find(query))

        # Get all unique tags for the filter dropdown
        tags = mongo_blogs.db.blogs_lists.distinct('tags')

        # Render the filtered blogs to the UI
        return render_template('blog.html', blogs=blogs, tags=tags)

    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500



if __name__ == "__main__":
    app.run(debug=True)