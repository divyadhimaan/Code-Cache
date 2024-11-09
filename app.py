from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient, errors
import os
from dotenv import load_dotenv
import certifi
from werkzeug.utils import secure_filename
from models import Question  
import markdown

load_dotenv()

app = Flask(__name__)

# Set the upload folder and allowed extensions
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'md'}

# Connect to MongoDB Atlas with error handling
try:
    client = MongoClient(
        os.getenv("MONGO_URI"),
        ssl=True,
        tlsCAFile=certifi.where()  # Use certifi's certificates
    )
    db = client['code_cache']
    collection = db['questions']
except errors.ConnectionError as e:
    print(f"Database connection failed: {e}")
    db = None
    collection = None
except Exception as e:
    print(f"An unexpected error occurred while connecting to the database: {e}")
    db = None
    collection = None

PREDEFINED_TOPICS = [
    'Arrays', 
    'Strings', 
    'Linked List', 
]

DIFFICULTY_LEVELS = [
    'Very Easy',
    'Easy',
    'Medium',
    'Hard',
    'Very Hard'
]

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500


# Function to check file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    print("on index page")
    return render_template('index.html')

# Route to display questions and filter by topic
@app.route('/view_cache')
def view_cache():
    try:
        selected_topics = request.args.getlist('topic')
        selected_tag = request.args.get('tag')
        
        if not selected_topics:
            selected_topics = ['All']
        
        if 'All' in selected_topics:
            questions = collection.find() if collection is not None else []
        else:
            questions = collection.find({"topic": {"$in": selected_topics}}) if collection is not None else []
            
        if selected_tag and selected_tag != 'All':
            questions = collection.find({"additional_tags": selected_tag}) if collection is not None else []
            
        
        
        tags = db['tags'].find()
        return render_template('view_cache.html', questions=questions, topics=PREDEFINED_TOPICS, selected_topics=selected_topics,tags=tags, selected_tag=selected_tag)
    
    except Exception as e:
        return render_template('500.html', error=str(e)), 500


@app.route('/question/<question_id>')
def view_question(question_id):
    try:
        question = collection.find_one({'question_id': int(question_id)}) if collection is not None else None
        if question:
            # Convert Markdown content to HTML
            notes_html = markdown.markdown(question['notes'])
            return render_template('view_question.html', question=question, notes_html=notes_html)
        return render_template('404.html'), 404
    except Exception as e:
        return render_template('500.html', error=str(e)), 500


# Route to add new question
@app.route('/add', methods=['GET', 'POST'])
def add_question():
    try:
        if request.method == 'POST':
            # Get the latest question count and generate the next ID
            question_count = collection.count_documents({}) if collection is not None else 0
            question_id = question_count + 1  # Generate the next available ID

            topics = request.form.getlist('topic')
            difficulty = request.form['difficulty']
            revision = request.form.get('revision', False)
            link = request.form['link']
            notes_file = request.files.get('notes_file')
            notes_content = ""
            
            additional_tags = request.form.getlist('additional_tags')
            new_tag = request.form.get('new_tag')
            if new_tag:
                additional_tags.append(new_tag)

            # If a notes file is uploaded, validate and process it
            if notes_file and allowed_file(notes_file.filename):
                # Create the upload directory if it doesn't exist
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])

                filename = secure_filename(notes_file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                notes_file.save(file_path)

                # Read file content
                with open(file_path, 'r') as file:
                    notes_content = file.read()

            # Create the new question document, with or without notes content
            question = Question(
                question_id=question_id,
                question_title=request.form['question_title'],
                topic=', '.join(topics),
                difficulty=difficulty,
                revision=revision,
                link=link,
                notes=notes_content ,
                additional_tags=additional_tags
            )

            # Insert the question into the collection
            if collection is not None:
                collection.insert_one(question.model_dump())
            return redirect(url_for('view_cache'))

        # If GET request, render the form
        tags = db['tags'].find()
        print("Tags: %s", tags)
        return render_template('add_question.html', topics=PREDEFINED_TOPICS, difficulties=DIFFICULTY_LEVELS,tags=tags)

    except Exception as e:
        return render_template('500.html', error=str(e)), 500

@app.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    try:
        question = collection.find_one({"question_id": question_id}) if collection is not None else None

        if request.method == 'POST':
            # Get form data to update the question
            updated_question = {
                "question_title": request.form['question_title'],
                "topic": request.form.getlist('topic'),
                "difficulty": request.form['difficulty'],
                "revision": request.form.get('revision', False),
                "link": request.form['link'],
            }

            # Handle optional notes file update
            notes_file = request.files.get('notes_file')
            if notes_file and allowed_file(notes_file.filename):
                filename = secure_filename(notes_file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                notes_file.save(file_path)
                with open(file_path, 'r') as file:
                    updated_question['notes'] = file.read()
                    
            current_tags = question.get('additional_tags', [])

            # Get new tags entered by the user and ensure no duplicates
            new_tags = request.form.getlist('additional_tags')
            new_tag = request.form.get('new_tag')
            updated_tags = list(set(current_tags + new_tags))  # Combine and remove duplicates

            # Update the question with the new tags
            updated_question['additional_tags'] = updated_tags
            
            if collection is not None:
                collection.update_one({"question_id": question_id}, {"$set": updated_question})
            return redirect(url_for('view_cache'))

        return render_template('add_question.html', 
                               question=question,
                               topics=PREDEFINED_TOPICS, 
                               difficulties=DIFFICULTY_LEVELS,
                               edit_mode=True,
                               selected_tags=question.get('additional_tags', []),
                               tags=db['tags'].find(),
                               new_tag_option=True)
    
    except Exception as e:
        return render_template('500.html', error=str(e)), 500


@app.route('/update_revision', methods=['GET'])
def update_revision():
    try:
        question_id = int(request.args.get('question_id'))
        status = int(request.args.get('status'))

        # Update the revision status in the database
        if collection is not None:
            result = collection.update_one(
                {'question_id': question_id},
                {'$set': {'revision': status}}
            )

            if result.matched_count > 0:
                return jsonify({'status': 'success', 'revision': status})
            else:
                return jsonify({'status': 'error', 'message': 'Question not found'}), 404
        else:
            return jsonify({'status': 'error', 'message': 'Database not available'}), 500

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/add_tag', methods=['POST'])
def add_tag():
    try:
        tag_name = request.form['tag_name']
        # Check if tag already exists in the database
        existing_tag = db['tags'].find_one({'tag_name': tag_name})
        
        if not existing_tag:
            db['tags'].insert_one({'tag_name': tag_name})
            return jsonify({'status': 'success', 'message': 'Tag added successfully!'})
        else:
            return jsonify({'status': 'error', 'message': 'Tag already exists!'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
