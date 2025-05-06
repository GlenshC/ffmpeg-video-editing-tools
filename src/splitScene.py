import os
import subprocess
import sys
import re
from concurrent.futures import ThreadPoolExecutor

#   this python script is just the split_video_on_transitions() function
#   all the other functions are just helpers
#   example:
#   split_video_on_transitions("in", "out", 0.15, 1.5, 8, 0, 0)


def split_large_video(video_file, chunk_length=120, temp_dir="temp_chunks"):
    """
    Splits a large video into smaller chunks of a fixed duration (in seconds).
    """
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    chunk_files = []
    ffmpeg_split_cmd = [
        "ffmpeg", "-hwaccel", "cuda", "-i", video_file, "-c:v", "copy", "-an",
        "-map", "0", "-segment_time", str(chunk_length), "-f", "segment",
        os.path.join(temp_dir, "chunk_%03d.mp4")
    ]
    try:
        subprocess.run(ffmpeg_split_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        chunk_files = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.startswith("chunk_")]
    except subprocess.CalledProcessError:
        print(f"Failed to split video: {video_file}")

    return sorted(chunk_files)


def process_clip(start, end, video_file, output_file):
    ffmpeg_split_cmd = [
        "ffmpeg",
        "-hwaccel", "cuda",
        "-i", video_file,
        "-ss", f"{start}",
        "-to", f"{end}",
        "-c:v", "h264_nvenc",
        "-preset", "p1",
        "-cq", "28",
        "-g", "999",
        "-bf", "0",
        "-an",
        output_file
    ]

    subprocess.run(ffmpeg_split_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def process_chunk(chunk_file, output_dir, scene_threshold=0.3, min_sec=1.5, max_sec=10, offset_start=0.1, offset_end=0.2):
    """
    Processes a single video chunk to split it into clips based on scene transitions.
    """
    base_name = os.path.splitext(os.path.basename(chunk_file))[0]
    file_extension = os.path.splitext(chunk_file)[1]

    scene_cache_file = os.path.join(output_dir, f"{base_name}_scenes.txt")
    if os.path.exists(scene_cache_file):
        print(f"Loading cached scenes for: {chunk_file}")
        with open(scene_cache_file, "r") as cache_file:
            timestamps = [float(line.strip()) for line in cache_file]
    else:
        print(f"Detecting transitions in: {chunk_file}...")
        scene_timestamps_file = "scene_timestamps.txt"
        # ffmpeg_scene_cmd = [
        #     "ffmpeg", "-hwaccel", "cuda", "-i", chunk_file, "-filter_complex",
        #     f"select='gt(scene,{scene_threshold})',metadata=print",
        #     "-vsync", "vfr", "-f", "null", "-"
        # ]
        ffmpeg_scene_cmd = [
            "ffmpeg", "-hwaccel", "cuda", "-i", chunk_file, "-filter_complex",
            f"select='gt(scene,{scene_threshold})',showinfo",
            "-vsync", "vfr", "-f", "null", "-"
        ]
        
        try:
            with open(scene_timestamps_file, "w") as scene_file:
                subprocess.run(ffmpeg_scene_cmd, stderr=scene_file, stdout=subprocess.DEVNULL, text=True, check=True)
        except subprocess.CalledProcessError:
            print(f"Failed to process chunk: {chunk_file}")
            return
            
        timestamps = []
        with open(scene_timestamps_file, "r") as file:
            for line in file:
                match = re.search(r"pts_time:([0-9.]+)", line)
                if match:
                    timestamps.append(float(match.group(1)))
        os.remove(scene_timestamps_file)
        
        if not timestamps:
            print(f"No transitions detected in: {chunk_file}. Skipping...")
            return
        
        with open(scene_cache_file, "w") as cache_file:
            for ts in timestamps:
                cache_file.write(f"{ts}\n")

    timestamps = [0.0] + timestamps
    video_duration_cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
        "format=duration", "-of", "csv=p=0", chunk_file
    ]
    video_duration = float(subprocess.check_output(video_duration_cmd).decode().strip())
    timestamps.append(video_duration)

    with ThreadPoolExecutor(max_workers=4) as executor:
        i = 0
        while i < len(timestamps) - 1:
            start = timestamps[i] + offset_start
            end = timestamps[i + 1] - offset_end
            
            while end - start > max_sec:  # Further split if too long
                mid = start + max_sec
                output_file = os.path.join(output_dir, f"{base_name}_clip_{i + 1}{file_extension}")
                executor.submit(process_clip, start, mid, chunk_file, output_file)
                start = mid
                i += 1
            
            if end - start >= min_sec:
                output_file = os.path.join(output_dir, f"{base_name}_clip_{i + 1}{file_extension}")
                executor.submit(process_clip, start, end, chunk_file, output_file)
            i += 1
    # Cleanup: Remove the scene cache file
    if os.path.exists(scene_cache_file):
        os.remove(scene_cache_file)
        print(f"Deleted scene cache file: {scene_cache_file}")



def split_video_on_transitions(input_folder, output_dir="output_clips", scene_threshold=0.3, min_sec=2, max_sec=10, offset_start=0.1, offset_end=0.2):
    """
    Splits videos based on transitions detected using FFmpeg's scene filter.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    valid_extensions = (".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv")
    input_files = [os.path.join(input_folder, f) for f in os.listdir(input_folder) 
                   if f.lower().endswith(valid_extensions)]

    if not input_files:
        print(f"No video files found in the folder: {input_folder}")
        return

    for video_file in input_files:
        print(f"Processing video: {video_file}...")
        
        # Step 1: Split large videos into 5-minute chunks
        temp_dir = os.path.join(output_dir, "temp_chunks")
        chunk_files = split_large_video(video_file, temp_dir=temp_dir)
        
        # Step 2: Process each chunk for scene detection and splitting
        for chunk_file in chunk_files:
            process_chunk(chunk_file, output_dir, scene_threshold, min_sec, max_sec, offset_start, offset_end)
        
        # Cleanup temporary files
        for temp_file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, temp_file))
        os.rmdir(temp_dir)
        
    print(f"All clips saved to: {output_dir}")
    
split_video_on_transitions("in", "out", 0.15, 1.5, 8, 0, 0)
