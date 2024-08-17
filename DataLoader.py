import csv
import yt_dlp
import os
import subprocess

def download_and_trim_audio(youtube_id, start_time, label, split, output_dir, clip_duration=3):
    url = f"https://www.youtube.com/watch?v={youtube_id}"
    output_filename = f"{youtube_id}_{start_time}_{label}.wav"
    output_path = os.path.join(output_dir, split, output_filename)
    temp_output_path = os.path.join(output_dir, split, f"temp_{output_filename}")
    
    ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'wav',
    }],
    'outtmpl': temp_output_path,
    'keepvideo': True,  # Add this option
	}


    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # 使用 FFmpeg 裁剪音频
        ffmpeg_command = [
            'ffmpeg',
            '-i', temp_output_path,
            '-ss', str(start_time),
            '-t', str(clip_duration),
            '-acodec', 'pcm_s16le',
            '-ar', '44100',
            output_path
        ]
        subprocess.run(ffmpeg_command, check=True)

        # 删除临时文件
        os.remove(temp_output_path)

        print(f"成功下载并裁剪: {youtube_id} - {label} ({split})")
        return True
    except Exception as e:
        print(f"处理 {youtube_id} 时发生错误: {str(e)}")
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)
        return False

def download_vggsound(csv_file, output_dir, clip_duration=3):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            youtube_id, start_time, label, split = row
            split_dir = os.path.join(output_dir, split)
            if not os.path.exists(split_dir):
                os.makedirs(split_dir)
            
            download_and_trim_audio(youtube_id, int(start_time), label, split, output_dir, clip_duration)


csv_file = 'vggsound.csv' 
output_dir = 'vggsound_dataset' 
clip_duration = 3
download_vggsound(csv_file, output_dir, clip_duration)