import json
import sys
from googleapiclient.discovery import build
#change this to match your own path into the folder
sys.path.append("Users/florin/PycharmProjects/NeuMovies/Youtube")

#what we need to connnect to the YT API
#if you get an authentification error, let me know and I'll give you another Developer KEY
DEVELOPER_KEY = "AIzaSyBvotJhVy4YOTrwR6_8FadrsYwEcQ636jI"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def youtube_search(q, max_results=50, order="relevance", token=None, location=None, location_radius=None):

  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    developerKey=DEVELOPER_KEY)

  search_response = youtube.search().list(
    q=q,
    type="video",
    pageToken=token,
    order=order,
    part="id,snippet",
    maxResults=max_results,
    location=location,
    locationRadius=location_radius

  ).execute()


  videos = []

  for search_result in search_response.get("items", []):
    if search_result["id"]["kind"] == "youtube#video":
      videos.append(search_result)
  try:
      nexttok = search_response["nextPageToken"]
      return(nexttok, videos)
  except Exception as e:
      nexttok = "last_page"
      return(nexttok, videos)

# Remove keyword arguments that are not set
def remove_empty_kwargs(**kwargs):
    good_kwargs = {}
    if kwargs is not None:
        for key, value in kwargs.iteritems():
            if value:
                good_kwargs[key] = value
    return good_kwargs

#makes the API call to get the comment threads for each video
def comment_threads_list_by_video_id(**kwargs):

    kwargs = remove_empty_kwargs(**kwargs)

    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)

    response = youtube.commentThreads().list(
        **kwargs
    ).execute()

    return response

#searches for videos that match some key words
def search_for_videos(keywords):

    #will be a tuple of length 2
    #the first is the search token, the second is the video information
    search_results = youtube_search(keywords)
    videos_info = search_results[1]

    video_ids = []

    for video in videos_info:
        #output_info.append(video['snippet'])
        video_ids.append(video['id'])

    # when we repeat the youtube_search, it will know where it left off
    # use youtube_search('string', token=token)

    #save the video IDs in a file just in case
    output_json(video_ids, 'video_ids')

    return video_ids

#outputs a json file
def output_json(data, file_name):
    with open('%s.txt' % file_name, 'w') as outfile:
        json.dump(data, outfile)

#need to convert the arguments into one string to send to the API
def search_for(strings):
    name = ''
    for i in strings:
        name += i
        name += ' '
    return name[:-1]

def main(args):

    #this will contain all info about a comment
    comments_to_output = []
    #this will contain the actual text from a comment
    final_comments = []

    name = search_for(args)

    vid_ids = search_for_videos(name)

    for id in vid_ids:
        # print id[u'videoId']
        #the u'text' notation has to do with the UTF encoding (look on stackoverflow to see what that is)
        comments_to_output.append(comment_threads_list_by_video_id(part='snippet,replies', videoId=id[u'videoId']))

    #if you output a comments_to_output to a json and then visualize it, you'll see how the tree works
    for j in range(len(comments_to_output)):
        for i in range(len(comments_to_output[j][u'items'])):
            final_comments.append(
                comments_to_output[j][u'items'][i][u'snippet'][u'topLevelComment'][u'snippet'][u'textOriginal'])

    output_json(final_comments, 'comments_%s' % name)

#run by typing in the Terminal: python YoutubeCall.py name of the search
if __name__ == '__main__':
    main(sys.argv[1:])