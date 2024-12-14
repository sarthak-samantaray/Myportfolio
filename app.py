from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename


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
    blogs = mongo.db.blogs_lists.find()
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
    return render_template('about.html') 


################################## BLOG OPERATIONS ####################################
# Add Blog Page
# Ensure the upload folder exists
import os
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route("/add", methods=["GET", "POST"])
def add_blog():
    if request.method == "POST":
        title = request.form.get("title")
        tags = request.form.get("tags").split(",")
        description = request.form.get("description")
        
        # Handle file upload
        if 'image' not in request.files:
            return "No file part", 400
        file = request.files['image']
        if file.filename == '':
            return "No selected file", 400
        
        # Secure the filename and save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Create the URL for the uploaded image
        image_url = url_for('static', filename='uploads/' + filename)

        # Create a new blog entry
        new_blog = {
            "title": title,
            "image_url": image_url,
            "tags": tags,
            "description": description
        }
        
        mongo.db.blogs_lists.insert_one(new_blog)
        return redirect(url_for("blog"))  # Redirect to the blog list page

    return render_template("add_blog.html")

# Delete Blog Route
@app.route("/delete/<blog_id>", methods=["POST"])
def delete_blog(blog_id):
    if mongo is None:
        return "Database connection error", 500  # Handle connection error
    mongo.db.blogs_lists.delete_one({"_id": ObjectId(blog_id)})
    return redirect(url_for("blog"))

###################################################################################

if __name__ == "__main__":
    app.run(debug=True)