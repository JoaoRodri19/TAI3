import os
import subprocess
import sys
import shutil
import argparse
import zipfile
import re
import zstandard as zstd
from pathlib import Path

def extract_segment(start_time, duration, input_dir="../complete_musics", output_format=None, quiet=True, output_dir="../segment_of_music"):
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
                    
def add_noise(input_dir, output_dir, type_of_noise, noise_percentage, quiet=False):
    os.makedirs(output_dir, exist_ok=True)
    for file_name in os.listdir(input_dir):
        input_file_path = os.path.join(input_dir, file_name)
        output_file_path = os.path.join(output_dir, file_name)
        
        generate_noise_command = [
            'sox', input_file_path, '-p', 'synth', type_of_noise, 'vol', noise_percentage
        ]
        
        # Command to mix the original file with the piped noise file
        mix_noise_command = [
            'sox', '-m', input_file_path, '-p', output_file_path
        ]

        # Open a subprocess to handle piping
        p1 = subprocess.Popen(generate_noise_command, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(mix_noise_command, stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits
        p2.communicate()  # Wait for process to complete

def create_signature(output_dir="../signature",input_dir="../complete_musics"):
    if not os.path.exists('../GetMaxFreqs/bin/GetMaxFreqs'):
        command = [
            'g++', '-W', '-Wall', '-std=c++11', '-o', '../GetMaxFreqs/bin/GetMaxFreqs',
            '../GetMaxFreqs/src/GetMaxFreqs.cpp', '-lsndfile', '-lfftw3', '-lm'
        ]
        subprocess.run(command, check=True)
  
        
    os.makedirs(output_dir, exist_ok=True)
    for file_name in os.listdir(input_dir):
        file_path = os.path.join(input_dir, file_name)
        file_root, file_ext = os.path.splitext(file_name)
        command = [
        '../GetMaxFreqs/bin/GetMaxFreqs', '-w', output_dir+'/'+file_root+'.freqs', file_path
        ]
        try:
            subprocess.run(command, check=True)
   
        except subprocess.CalledProcessError as e:
            print(f"Error craeting signature {file_name}: {e}")
        
def zip_file(file, output_dir, compression,compression_level = None):
    if compression_level!=None:
        compression_level = int(compression_level)
    file_name_with_extension = os.path.basename(file)
    file_name = os.path.splitext(file_name_with_extension)[0]
    if compression == "gzip":
        compression = zipfile.ZIP_DEFLATED
    elif compression == "bzip2":
        compression= zipfile.ZIP_BZIP2
    elif compression == "lzma":
        compression= zipfile.ZIP_LZMA
    elif compression == "zstd":
        with open(file, 'rb') as f_in:
            with open(output_dir+'/'+file_name+".zip", 'wb') as f_out:
                if compression_level == None:
                    cctx = zstd.ZstdCompressor()
                else:
                    cctx = zstd.ZstdCompressor(level=compression_level)
                f_out.write(cctx.compress(f_in.read()))
                return
    
    
    
    if compression == "zstd":
        with zipfile.ZipFile(output_dir+'/'+file_name+".zip", 'w') as zipf:
            zipf.write(file)
        os.remove(os.path.join(output_dir,file_name+".freqs.zst"))
    else:
        with zipfile.ZipFile(output_dir+'/'+file_name+".zip", 'w', compression,compresslevel=compression_level) as zipf:
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

def compress_data_base(compression,complete_musics ="../signature",output_compress="../compressed",compression_level=None):
    os.makedirs(output_compress, exist_ok=True)
    for file_name in os.listdir(complete_musics):
        file_path = os.path.join(complete_musics ,file_name)
        zip_file(file_path,output_compress,compression,compression_level)
        
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
            os.remove(file_path)

def predict(file,compression,signatures_complete="../signature"
            ,output_dir="../compressed_together",compressed_files = "../compressed",compression_level=None):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    #signature of target
    file_path_obj = Path(file)
    file_name_without_extension = file_path_obj.stem
    command = [
        '../GetMaxFreqs/bin/GetMaxFreqs', '-w', "./"+file_name_without_extension+'.freqs', file
        ]
    subprocess.run(command, check=True)
    file = file_name_without_extension+".freqs"
    
    append_files(file,signatures_complete,output_dir)
    #compress appended files
    
    for file_name in os.listdir(output_dir):
        file_path = os.path.join(output_dir ,file_name)
        zip_file(file_path,output_dir,compression,compression_level=compression_level)
    
    delete_files_with_extension(output_dir,".freqs")
    
    #print(file)
    zip_file(file,".",compression,compression_level)
    os.remove(file)
    
    file = file_name_without_extension+".zip"
    #print(file)
    sizes = dict()
    target_size = os.path.getsize(file)
    #print("\nTarget:",target_size)
    for file_name in os.listdir(output_dir):
        file_path = os.path.join(output_dir ,file_name)
        file_root, file_ext = os.path.splitext(file_name)
        sizes[file_root] = os.path.getsize(file_path)
    #print("Sizes:",sizes)
    # find max similarity
    min_sim = float('inf'),""
    sim_list = dict()
    for file_name in os.listdir(compressed_files):
        file_path = os.path.join(compressed_files ,file_name)
        file_root, file_ext = os.path.splitext(file_name)
        size = os.path.getsize(file_path)
        sim_list[file_root] = NCD(target_size,size,sizes[file_root])
        if sim_list[file_root] < min_sim[0]:
            min_sim = (sim_list[file_root],file_root)
    
    for key, value in sim_list.items():
        print(f"{key}: {value}")
    print("Segmented file: ",file_name_without_extension)
    print("Prediction: ",min_sim[1])
    
    os.remove(file)
    #if file_name_without_extension == min_sim[1].removesuffix(".freqs"):
    #    return True
    return min_sim[1].removesuffix(".freqs")
    
    
def NCD(seg,complete,mix):
    return (mix - min(seg,complete))/max(seg,complete)  
def clean():
    dirs = ["../compressed","../segment_of_music","../signature","../compressed_together","../noise","../temp_input_dir"]   
    for dir in dirs:
        if os.path.exists(dir):
            shutil.rmtree(dir)  
    for file_name in os.listdir("."):
        if file_name not in ["run.py","run.sh","prepare.sh","predict.sh","clean.sh","add_noise.sh","results.txt","graphs.ipynb"]:
            os.remove(file_name)
            
            
def grid_search():
    compression_modes = ["gzip", "bzip2", "lzma","zstd"]
    #compression_modes = ["lzma"]
    types_of_noise = ["white", "pink", "brown"] # "blue", "violet", "grey" not working for unknown reason
    #types_of_noise = ["white"]
    segment_lengths = ["10", "30", "60"]
    #segment_lengths = ["20"]
    noise_percentages = ["0.00", "0.01", "0.05", "0.10", "0.25", "0.50","0.80"]
    #noise_percentages = ["0"]
    compression_levels = [None,2,5,9]
    #compression_levels = [5]
    
    
    
    complete_wav_files_input_dir = "../complete_musics"
    preds = {}
    with open("results.txt","w") as results_file:
        results_file.write("Type of noise\tNoise Percentage\tCompression Mode\tCompression Level\tSegment Length\tPredicts\n")
        for type_of_noise in types_of_noise:
            for noise_percentage in noise_percentages:
                add_noise(input_dir=complete_wav_files_input_dir, output_dir="../temp_input_dir",type_of_noise=type_of_noise,noise_percentage=noise_percentage)
                for compression_mode in compression_modes:
                    for segment_length in segment_lengths:
                        for compression_level in compression_levels:
                            extract_segment(start_time=5, duration=segment_length, input_dir=complete_wav_files_input_dir)
                            create_signature(input_dir=complete_wav_files_input_dir)
                            compress_data_base(compression=compression_mode,compression_level=compression_level)
                            
                            for file_name in os.listdir("../segment_of_music"):
                                preds[file_name.removesuffix(".wav")] =  predict(file=os.path.join("../segment_of_music",file_name),compression=compression_mode,compression_level=compression_level)
                            results_file.write(f"{type_of_noise}\t\t\t{noise_percentage}\t\t\t\t\t{compression_mode}\t\t\t\t{compression_level}\t\t\t\t{segment_length}\t\t\t\t{preds}\n")
                    clean()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audio processing script with optional segment extraction.")
    subparsers = parser.add_subparsers(dest='command', required=True, help='Sub-command help')

    # Subparser for the 'seg' command
    parser_seg = subparsers.add_parser('seg', help='Extract segment from audio files')
    parser_seg.add_argument('input_dir', type=str, help="Input directory containing audio files")
    parser_seg.add_argument('start_time', type=float, help="Start time for the segment to extract (in seconds)")
    parser_seg.add_argument('duration', type=float, help="Duration of the segment to extract (in seconds)")
    parser_seg.add_argument('-f', '--format', type=str, help="Output audio format (e.g., mp3, wav)")
    parser_seg.add_argument('-q', '--quiet', action='store_true', help="Suppress output messages")

    parser_sig = subparsers.add_parser('sig', help='Create music signature')
    parser_sig.add_argument('input_dir', type=str, help="Input directory containing audio files")

    parser_compress = subparsers.add_parser('compress', help='compress database of complete musics')
    parser_compress.add_argument('compression', type=str, help="Compression method")
    parser_compress.add_argument('compression_lvl', type=str, help="Compression level")
    
    parser_pred = subparsers.add_parser('pred', help='Predict to music given a segment')
    parser_pred.add_argument('target_file', type=str, help="Segment of music to predict")
    parser_pred.add_argument('compression', type=str, help="Compression method")
    parser_pred.add_argument('compression_lvl', type=str, help="Compression level")

    parser_clean = subparsers.add_parser('clean', help='Clean all musics except database')
    
    parser_add_noise = subparsers.add_parser('add_noise', help='Adds noise to all files in a directory')
    parser_add_noise.add_argument('input_dir', type=str, help="")
    parser_add_noise.add_argument('type_of_noise', type=str, help="")
    parser_add_noise.add_argument('percentage_noise', type=str, help="")
    parser_add_noise.add_argument('-q', '--quiet', action='store_true', help="Suppress output messages")
    
    parser_grid_search = subparsers.add_parser('grid_search')
    
    args = parser.parse_args()

    if args.command == 'seg':
        extract_segment( args.start_time, args.duration,args.input_dir, args.format, args.quiet)
    if args.command == 'sig':
        create_signature(input_dir=args.input_dir)
    if args.command == 'compress':
        compress_data_base(args.compression,compression_level=args.compression_lvl)
    if args.command == "pred":
        predict(args.target_file,args.compression,compression_level=args.compression_lvl)
    if args.command == "clean":
        clean()
    if args.command == "add_noise":
        add_noise(args.input_dir, "../noise", args.type_of_noise, args.percentage_noise, args.quiet)
    if args.command == "grid_search":
        grid_search()