from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost
from wordpress_xmlrpc.methods.taxonomies import GetTerms
from wordpress_xmlrpc.methods.media import UploadFile
from wordpress_xmlrpc.methods.media import GetMediaLibrary
from wordpress_xmlrpc.methods.posts import DeletePost
from wordpress_xmlrpc.methods.posts import GetPosts
from datetime import datetime, timedelta
import collections
import sys
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

# Fix for deprecated Iterable in newer Python versions
if not hasattr(collections, 'Iterable'):
    import collections.abc
    collections.Iterable = collections.abc.Iterable

# WordPress credentials and URL (replace with actual details)
WP_URL = "https://articlesummarizer1.wordpress.com/xmlrpc.php"
WP_USER = "pkulkarni0007"
WP_PASSWORD = "A2US#8#agAFcQ6d"

def add_read_more(content):
    """Inserts a WordPress 'Read More' tag after 30 words."""
    words = content.split()
    if len(words) > 30:
        return " ".join(words[:30]) + " <!--more--> " + " ".join(words[30:])
    return content

def post_to_wordpress(title, content, categories=None):
    """Posts content to WordPress with a 'Read more' feature."""
    
    wp = Client(WP_URL, WP_USER, WP_PASSWORD)

    # Create the WordPress post object
    post = WordPressPost()
    post.title = title
    post.content = add_read_more(content)  # Insert "Read more" correctly
    post.terms_names = {'category': categories} if categories else {}
    post.post_status = 'publish'

    # Publish the post
    post_id = wp.call(NewPost(post))

    print(f"Post published successfully: https://yourwordpresssite.com/?p={post_id}")
    return post_id

def resize_image(image_path, max_width, max_height):
    """Resizes an image while maintaining aspect ratio."""
    img = Image.open(image_path)
    
    # Resize while maintaining aspect ratio
    img.thumbnail((max_width, max_height))
    
    # Save the resized image (overwrite or new file)
    resized_path = image_path.replace(".jpg", "_resized.jpg")  # Save with new name
    img.save(resized_path, format="JPEG", quality=90)  # Adjust quality if needed
    
    return resized_path  # Return the new path

def post_with_image(title, content, image_path, categories = None):
    # Connect to WordPress
    resized_image = resize_image(image_path, max_width = 324, max_height=324)
    wp = Client(WP_URL, WP_USER, WP_PASSWORD)

    # Upload Image
    with open(resized_image, "rb") as img:
        data = {
            "name": "uploaded_image.png",
            "type": "image/png",
            "bits": img.read(),
        }
    
    response = wp.call(UploadFile(data))  # Upload image to WordPress media
    image_url = response["url"]  # Get uploaded image URL

    # Create Post
    post = WordPressPost()
    post.title = title
    post.content = add_read_more(f'<img src="{image_url}" alt="Image"><br>{content}')  # Add image to content
    post.terms_names = {'category': categories} if categories else {}
    post.post_status = "publish"  # Change to "draft" if you don't want to publish immediately

    wp.call(NewPost(post))  # Publish post

    print(f"✅ Post published: {title} (Image: {image_url})")

def delete_post(post_id):
    """Deletes a WordPress post by its ID."""
    wp = Client(WP_URL, WP_USER, WP_PASSWORD)
    
    try:
        wp.call(DeletePost(post_id))
        print(f"Post with ID {post_id} deleted successfully.")
    except Exception as e:
        print(f"Failed to delete post {post_id}: {e}")

def get_post_id_by_title(title):
    """Finds a WordPress post ID by its title."""
    wp = Client(WP_URL, WP_USER, WP_PASSWORD)
    posts = wp.call(GetPosts({'number': 10}))  # Get latest 10 posts

    for post in posts:
        if post.title == title:
            return post.id

    return None  # Post not found

def delete_post_by_title(title):
    """Finds a post by title and deletes it."""
    post_id = get_post_id_by_title(title)
    if post_id:
        delete_post(post_id)
    else:
        print(f"No post found with title '{title}'.")

def delete_old_posts(days=7):
    """Deletes posts older than a certain number of days."""
    wp = Client(WP_URL, WP_USER, WP_PASSWORD)
    cutoff_date = datetime.now() - timedelta(days=days)

    posts = wp.call(GetPosts({'number': 20}))  # Fetch latest 20 posts

    for post in posts:
        post_date = datetime.strptime(post.date.strftime('%Y-%m-%d'), '%Y-%m-%d')
        if post_date < cutoff_date:
            print(f"Deleting post '{post.title}' (ID: {post.id}) from {post_date}")
            delete_post(post.id)

def delete_all_posts():
    """Fetches and deletes all posts from WordPress."""
    wp = Client(WP_URL, WP_USER, WP_PASSWORD)

    # Fetch all posts (use 'number' to limit per call)
    posts = wp.call(GetPosts({'number': 100}))  # Adjust 'number' if needed

    if not posts:
        print("No posts found to delete.")
        return

    for post in posts:
        wp.call(DeletePost(post.id))
        print(f"Deleted post: {post.title}")


# Example usage
