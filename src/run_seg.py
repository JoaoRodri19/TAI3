import os
import subprocess
import sys
import argparse
import zipfile

def extract_segment(input_dir, output_dir, start_time, duration, output_format=None, quiet=False):
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Loop through each audio file in the input directory
    for file_name in os.listdir(input_dir):
        file_path = os.path.join(input_dir, file_name)
        # Check if the file is a regular file (not a directory)
        if os.path.isfile(file_path):
            # Modify the output file path to include the new format if specified
            if output_format:
                output_file_name = os.path.splitext(file_name)[0] + '.' + output_format
            else:
                output_file_name = file_name
            output_file_path = os.path.join(output_dir, output_file_name)
            
            # Construct the SoX command
            command = [
                'sox', file_path, output_file_path, 'trim', str(start_time), str(duration)
            ]
            
            # Execute the SoX command
            try:
                subprocess.run(command, check=True)
                if not quiet:
                    print(f"Processed {file_name}")
            except subprocess.CalledProcessError as e:
                if not quiet:
                    print(f"Error processing {file_name}: {e}")

def create_signature(output_dir,input_dir):
    command = [
        'g++', '-W', '-Wall', '-std=c++11', '-o', 'GetMaxFreqs',
        '../GetMaxFreqs/src/GetMaxFreqs.cpp', '-lsndfile', '-lfftw3', '-lm'
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error compiling GetMaxFreqs.cpp: {e}")
        
    os.makedirs(output_dir, exist_ok=True)
    for file_name in os.listdir(input_dir):
        file_path = os.path.join(input_dir, file_name)
        file_root, file_ext = os.path.splitext(file_name)
        command = [
        './GetMaxFreqs', '-w', output_dir+'/'+file_root+'.freqs', file_path
        ]
        try:
            subprocess.run(command, check=True)
   
        except subprocess.CalledProcessError as e:
            print(f"Error craeting signature {file_name}: {e}")
        
def zip_files(file_paths, zip_name, compression):
    with zipfile.ZipFile(zip_name, 'w', compression) as zipf:
        for file in file_paths:
            zipf.write(file)
           

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audio processing script with optional segment extraction.")
    subparsers = parser.add_subparsers(dest='command', required=True, help='Sub-command help')

    # Subparser for the 'seg' command
    parser_seg = subparsers.add_parser('seg', help='Extract segment from audio files')
    parser_seg.add_argument('input_dir', type=str, help="Input directory containing audio files")
    parser_seg.add_argument('output_dir', type=str, help="Output directory for processed audio files")
    parser_seg.add_argument('start_time', type=float, help="Start time for the segment to extract (in seconds)")
    parser_seg.add_argument('duration', type=float, help="Duration of the segment to extract (in seconds)")
    parser_seg.add_argument('-f', '--format', type=str, help="Output audio format (e.g., mp3, wav)")
    parser_seg.add_argument('-q', '--quiet', action='store_true', help="Suppress output messages")

    parser_sig = subparsers.add_parser('sig', help='Create music signature')
    parser_sig.add_argument('input_dir', type=str, help="Input directory containing audio files")
    parser_sig.add_argument('output_dir', type=str, help="Output directory for processed audio files")
    args = parser.parse_args()

    if args.command == 'seg':
        extract_segment(args.input_dir, args.output_dir, args.start_time, args.duration, args.format, args.quiet)
    if args.command == 'sig':
        create_signature(args.output_dir,args.input_dir)
