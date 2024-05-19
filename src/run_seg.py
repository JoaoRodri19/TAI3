import os
import subprocess
import sys
import argparse
import zipfile
from pathlib import Path
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
        
def zip_file(file, output_dir, compression):
    if compression == "gzip":
        compression = zipfile.ZIP_DEFLATED
    else:
        return
    file_name_with_extension = os.path.basename(file)
    file_name = os.path.splitext(file_name_with_extension)[0]
    with zipfile.ZipFile(output_dir+'/'+file_name+".zip", 'w', compression) as zipf:
        zipf.write(file)
        
def append_files(file, path_files, output_dir):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Read the contents of the initial binary file to be appended
    with open(file, 'rb') as f:
        initial_content = f.read()

    # Iterate over all files in the given directory
    for file_name in os.listdir(path_files):
        file_path = os.path.join(path_files, file_name)
        file_root, file_ext = os.path.splitext(file_name)
        
        # Read the content of the current binary file
        with open(file_path, 'rb') as f:
            additional_content = f.read()

        # Define the output file path
        output_file_path = os.path.join(output_dir, file_root + ".freqs")
        
        # Write the concatenated binary content to the output file
        with open(output_file_path, 'wb') as f:
            f.write(initial_content)
            f.write(additional_content)

        print(f"Successfully appended {file_name} to {output_file_path}")
def compress_data_base(complete_musics,output_compress,compression):
    os.makedirs(output_compress, exist_ok=True)
    for file_name in os.listdir(complete_musics):
        file_path = os.path.join(complete_musics ,file_name)
        zip_file(file_path,output_compress,compression)
def delete_files_with_extension(directory, extension):
    # Ensure the directory exists
    if not os.path.exists(directory):
        print(f"The directory {directory} does not exist.")
        return
    
    # Iterate over all files in the given directory
    for file_name in os.listdir(directory):
        # Check if the file ends with the specified extension
        if file_name.endswith(extension):
            file_path = os.path.join(directory, file_name)
            try:
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")

def predict(file,compression,signatures_complete="../signatures_complete"
            ,output_dir="../compressed_together",compressed_files = "../compressed_files"):
    append_files(file,signatures_complete,output_dir)
    #compress appended files
    for file_name in os.listdir(output_dir):
        file_path = os.path.join(output_dir ,file_name)
        zip_file(file_path,output_dir,compression)
    delete_files_with_extension(output_dir,".freqs")
    #signature of target
    file_path_obj = Path(file)
    file_name_without_extension = file_path_obj.stem
    command = [
        './GetMaxFreqs', '-w', "./"+file_name_without_extension+'.freqs', file
        ]
    subprocess.run(command, check=True)
    file = file_name_without_extension+".freqs"
    
    zip_file(file,".",compression)
    os.remove(file)
    file = file_name_without_extension+".zip"
    print(file)
    
  
    sizes = dict()
    target_size = os.path.getsize(file)
    for file_name in os.listdir(output_dir):
        file_path = os.path.join(output_dir ,file_name)
        file_root, file_ext = os.path.splitext(file_name)
        sizes[file_root] = os.path.getsize(file_path)
    # find max similarity
    min_sim = float('inf'),""
    sim_list = dict()
    for file_name in os.listdir(compressed_files):
        file_path = os.path.join(compressed_files ,file_name)
        file_root, file_ext = os.path.splitext(file_name)
        size = os.path.getsize(file_path)
        sim_list[file_root] = NCD(target_size,size,sizes[file_root])
        if sim_list[file_root] < min_sim[0]:
            min_sim = (size,file_root)
    print("Segment file:",file_name_without_extension)
    print("prediction:",min_sim[1])
def NCD(seg,complete,mix):
    return (mix - min(seg,complete))/max(seg,complete)  
   

           

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
    
    parser_sig = subparsers.add_parser('compress', help='compress database of complete musics')
    parser_sig.add_argument('musics_database', type=str, help="musics database")
    parser_sig.add_argument('out_compress', type=str, help="Output directory for the compressed musics")
    parser_sig.add_argument('compression', type=str, help="Compression method")
    
    parser_sig = subparsers.add_parser('pred', help='Predict to music given a segment')
    parser_sig.add_argument('target_file', type=str, help="musics database")
    parser_sig.add_argument('compression', type=str, help="Compression method")
    
    args = parser.parse_args()

    if args.command == 'seg':
        extract_segment(args.input_dir, args.output_dir, args.start_time, args.duration, args.format, args.quiet)
    if args.command == 'sig':
        create_signature(args.output_dir,args.input_dir)
    if args.command == 'compress':
        compress_data_base(args.musics_database,args.out_compress,args.compression)
    if args.command == "pred":
        predict(args.target_file,args.compression)
    
