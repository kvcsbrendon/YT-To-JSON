import os
import json
from datetime import datetime
from googleapiclient.discovery import build
import isodate

# 🔑 YouTube API key
# Replace this with your own API key
API_KEY = 'YOUR_API_KEY_HERE'

# 📁 Output directory for saving JSON files
# Replace this with your desired path
OUTPUT_DIR = 'YOUR_OUTPUT_DIRECTORY_PATH_HERE'

# Initialize YouTube API client
youtube = build('youtube', 'v3', developerKey=API_KEY)


def get_playlist_videos(playlist_id):
    videos = []
    next_page_token = None
    video_position = 1

    while True:
        try:
            request = youtube.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response['items']:
                try:
                    video_id = item['contentDetails']['videoId']

                    video_details = youtube.videos().list(
                        part='snippet,contentDetails,statistics',
                        id=video_id
                    ).execute()

                    video_info = video_details['items'][0]
                    snippet = video_info['snippet']
                    stats = video_info['statistics']
                    content_details = video_info['contentDetails']

                    duration_iso = content_details['duration']
                    duration_human = convert_duration_to_human_readable(duration_iso)

                    video_data = {
                        'ID': video_position,
                        'title': snippet['title'],
                        'viewCount': stats.get('viewCount', '0'),
                        'author': snippet['channelTitle'],
                        'length': duration_human,
                        'videoID': video_id,
                        'videoURL': f"https://www.youtube.com/watch?v={video_id}"
                    }
                    videos.append(video_data)
                    video_position += 1
                except Exception as e:
                    print(f"Error processing video ID {video_id}: {e}")

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        except Exception as e:
            print(f"Error fetching playlist {playlist_id}: {e}")
            break

    return videos


def get_playlist_name(playlist_id):
    try:
        request = youtube.playlists().list(
            part='snippet',
            id=playlist_id
        )
        response = request.execute()
        playlist_name = response['items'][0]['snippet']['title']
        return playlist_name
    except Exception as e:
        print(f"Error fetching playlist name for {playlist_id}: {e}")
        return f"UnknownPlaylist_{playlist_id}"


def convert_duration_to_human_readable(duration_iso):
    try:
        duration = isodate.parse_duration(duration_iso)
        total_seconds = int(duration.total_seconds())
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes}:{seconds:02d}"
    except Exception as e:
        print(f"Error converting duration {duration_iso}: {e}")
        return "Unknown"


def save_playlist_to_json(playlist_id, output_dir):
    videos = get_playlist_videos(playlist_id)
    playlist_name = get_playlist_name(playlist_id)
    current_date = datetime.now().strftime("%Y-%m-%d")
    filename = f"{playlist_name}_{current_date}.json"

    filename = "".join(c if c.isalnum() or c in " ._-" else "_" for c in filename)

    output_path = os.path.join(output_dir, filename)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=4)
    print(f"Playlist '{playlist_name}' saved to {output_path}")


def extract_playlist_ids(file_path):
    playlist_data = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            try:
                name, url_or_id = line.split(":", 1)
                name = name.strip()
                url_or_id = url_or_id.strip()

                if "list=" in url_or_id:
                    playlist_id = url_or_id.split("list=")[1].split("&")[0]
                else:
                    playlist_id = url_or_id

                playlist_data.append({"name": name, "id": playlist_id})
            except ValueError:
                print(f"Skipping invalid line: {line}")
    return playlist_data


if __name__ == "__main__":
    # 📄 Replace with the path to your own input file
    playlist_data = extract_playlist_ids("playlists.txt")

    for playlist in playlist_data:
        try:
            print(f"Processing playlist: {playlist['name']} (ID: {playlist['id']})")
            save_playlist_to_json(playlist['id'], OUTPUT_DIR)
        except Exception as e:
            print(f"Error processing playlist {playlist['name']} (ID: {playlist['id']}): {e}")
