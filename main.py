import ffmpeg._probe
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube
import os
import random
import ffmpeg
from ffprobe import FFProbe


def format_timestamp(seconds):
    """
    Converts seconds into SRT timestamp format (HH:MM:SS,mmm).
    Args:
        seconds (float): amount of seconds
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    milliseconds = int(seconds % 1 * 1000)
    return f"{hours:02.0f}:{minutes:02.0f}:{seconds:02.0f},{milliseconds:03d}"

def timestamp_to_seconds(time):
    """
    Converts the String timestamp e.g. "00:03:30.20" to its equivalence in seconds
    Args:
        time (String): Timestamp of video duration, outputted from FFProbe "HH:MM:SS.MS"
    """
    hours, minutes, seconds = time.split(':')
    hours = int(hours)
    minutes = int(minutes)
    seconds, milliseconds = seconds.split('.')
    seconds = int(seconds)
    milliseconds = int(milliseconds)
    total_seconds = hours * 3600 + minutes * 60 * seconds + milliseconds / 100
    return total_seconds


def getMainContent(videoID):
    """
    Downloads the Youtube Video specified in the URL to be stored in the /Content/mainContent Folder
    Downloads YouTube SRT file
    Returns the content Directory
    Args:
        videoID (String): YouTube Video ID 
    """
    #Create Main Content Directory: /Content/videoID 
    contentPath = os.path.join("Content", videoID)
    os.makedirs(contentPath, exist_ok=True)
    #Get SRT file of video
    try:
        transcript = YouTubeTranscriptApi.get_transcript(videoID)
        #Convert transcript to SRT formatted String
        print(transcript)
        srtData = ""
        for i, sub in enumerate(transcript): 
            start_seconds = sub.get('start', 0.0)
            end_seconds = start_seconds + sub.get('end', sub['duration'])
            start_time = format_timestamp(start_seconds)
            end_time = format_timestamp(end_seconds)
            srtData += f"{i+1}\n{start_time} --> {end_time}\n{sub['text']}\n\n"
        print(srtData)
        with open(os.path.join(contentPath, videoID + ".srt"), 'w') as srt_file:
            srt_file.write(srtData) 
    except Exception as e:
        print(f"Error retrieving transcript: {e}")
    #Download YouTube Video   
    yt = YouTube("https://www.youtube.com/watch?v="+videoID)
    ys = yt.streams.get_highest_resolution() 
    ys.download(contentPath, filename = videoID + ".mp4")



def subcontentLength(mainContentDuration,subContentDuration):
    """
    Returns a Tuple consisting of the (startTime, endTime) in seconds.
    This allows later functions to return a subclip of the Sub Content
    Args:
        subContentDuration(float): Length in Seconds of the Sub Content
        mainContentDuration(float): Length in Seconds of the Main Content
    """
    startTime = random.uniform(0, subContentDuration - mainContentDuration)
    endTime = startTime + mainContentDuration
    return (startTime, endTime)

def videoCreation(videoID):
    """
    Edits the main content with sub-content to create 9:16 video
    sub-content is spliced at a random point to match the duration of main content
    Main Content folder contains SRT file and MP4 file
    Args:
        videoID (String): Path of folder for main content video 
        subContentPath (String): Path of sub content video 
    """
    #Load name of random subcontent from directory
    randomSubContentName = os.listdir("SubContent")[random.randint(0, len(os.listdir("SubContent"))-1)]
    trimTuple = subcontentLength(timestamp_to_seconds(FFProbe("content/"+ videoID + "/" + videoID + ".mp4").metadata['Duration']), timestamp_to_seconds(FFProbe("SubContent/" + randomSubContentName).metadata['Duration']))
    mainContent = ffmpeg.input("Content/"+ videoID + "/" + videoID + ".mp4")
    subContent = ffmpeg.input("SubContent/" + randomSubContentName).trim(start_pts = trimTuple[0], end_pts = trimTuple[1])
    (
        ffmpeg
        .filter([mainContent, subContent], 'vstack')
        .output("Output/"+ videoID  + ".mp4", codec='libx264', crf=18)
        .global_args('-vf', "subtitles='" + "Content/" + videoID + "/" + videoID + ".srt':x=540:y=960" )
        .run()
    )

videoID = "a62rCSNvMJA"
#getMainContent(videoID)

videoCreation(videoID)
#videoCreation(, "SubContent\mcParkour.mp4")

