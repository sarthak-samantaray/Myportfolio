from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from bson import json_util
from flask import request
import json


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
        projects = mongo_projects.db.projects_lists.find()  # Fetch projects from the projects collection
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
    return render_template("blog.html", blogs=blogs_list)

# Blog Detail Page
@app.route("/blog/<blog_id>")
def blog_detail(blog_id):
    if mongo is None:
        return "Database connection error", 500  # Handle connection error
    blog = mongo.db.blogs_lists.find_one({"_id": ObjectId(blog_id)})
    return render_template("blog_detail.html", blog=blog)



@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/about') 
def about():
    skills = mongo_skills.db.skills_details.find()
    return render_template('about.html',skills=skills) 


################################## BLOG OPERATIONS ####################################


# Delete Blog Route
@app.route("/delete/<blog_id>", methods=["POST"])
def delete_blog(blog_id):
    if mongo is None:
        return "Database connection error", 500  # Handle connection error
    mongo.db.blogs_lists.delete_one({"_id": ObjectId(blog_id)})
    return redirect(url_for("blog"))

###################################################################################

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


def parse_markdown(md_content):
    """Parse Markdown content into a structured JSON format."""
    lines = md_content.splitlines()
    result = {
        'h1': '',
        'h2': '',
        'h3': '',
        'h4': '',
        'images': [],  # Use a list to store multiple images
        'code': '',
        'text': []
    }

    code_content = []
    is_code_block = False

    for line in lines:
        line = line.strip()

        # Handle headings
        if line.startswith('# '):
            result['h1'] = line[2:].strip()
        elif line.startswith('## '):
            result['h2'] = line[3:].strip()
        elif line.startswith('### '):
            result['h3'] = line[4:].strip()
        elif line.startswith('#### '):
            result['h4'] = line[5:].strip()

        # Handle images (append to list)
        elif line.startswith('!['):
            start = line.find('(') + 1
            end = line.find(')')
            if start > 0 and end > start:
                result['images'].append(line[start:end])

        # Handle code blocks
        elif line.startswith('```'):
            is_code_block = not is_code_block
            if not is_code_block and code_content:
                result['code'] = '\n'.join(code_content)
                code_content = []
        elif is_code_block:
            code_content.append(line)

        # Handle regular text
        elif line and not is_code_block:
            result['text'].append(line)

    return result



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
        return jsonify({'message': 'Blog saved successfully', 'id': str(result.inserted_id)}), 200

    except Exception as e:
        # Handle any unexpected errors
        return jsonify({'message': f'Error: {str(e)}'}), 500



if __name__ == "__main__":
    app.run(debug=True)