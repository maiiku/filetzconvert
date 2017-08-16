#!/usr/bin/python
from __future__ import print_function, unicode_literals

import sys, getopt, os, errno, shutil, re
import datetime
try:
    import pytz
except ImportError:
    print('This utility requires pytz. Please install it (pip install pytz)')
    sys.exit()


def help(short=False):
    basic_syntax = "filetzconvert.py --from-tz=<TZ_NAME> --to-tz=<TZ_NAME> --source-directory=<dir> --destination-directory=<dir> --mode=<copy|move>, --pattern=<pattern>"
    if short:
        return basic_syntax
    help_str = """
    {}

    This script renames and moves files that have time strings as names, converting date in each filename to proivded timezone.

    Accepted attributes:
    -h, --help: shows this help page
    -s, --source-directory: source folder, defaults to current folder
    -d, --destination-directory: destination folder, defaults to current folder
    -f, --from-tz: timezone of source file names, dafaults to UTC
    -t, --to-tz: timezone of destination file names, dafaults to UTC
    -m, --mode: 'copy' or 'move' files, defaults to copy
    -p, --pattern: filename pattern (without file extenstion), defaults to %y%d%m%H%M%S
    --dry-run: testing switch, when present no physical changes will be perfomed

    Example:
    filetzconvert.py -s ./src/ -d ./dst/ -t Europe/Warsaw --m move

    """.format(basic_syntax)
    return help_str


def validate(data):
    err_msgs = []
    if not os.path.isdir(data['src']):
        err_msgs.append('{path} is not a valid folder'.format(path=data['src']))
    try:
        data['from_tz'] = pytz.timezone(data['from_tz'])
    except pytz.UnknownTimeZoneError:
        err_msgs.append('{from_tz} is not a valid timezone'.format(path=data['from_tz']))
    try:
        data['to_tz'] = pytz.timezone(data['to_tz'])
    except pytz.UnknownTimeZoneError:
        err_msgs.append('{to_tz} is not a valid timezone'.format(path=data['to_tz']))


def run(data):
    msgs = []
    src_files = [
        os.path.split(f)[-1] 
        for f in os.listdir(data['src']) if os.path.isfile(os.path.join(data['src'], f))
    ]
    validated_files = []
    for filename in src_files:
        match = re.match('(\d{12})(\..+)', filename)
        if match and len(match.groups()) > 1:
            date_str = match[1]
            file_ext = match[2]
            try:
                from_dt = data['from_tz'].localize(
                    datetime.datetime.strptime(date_str, data['pattern'])
                )
            except ValueError:
                continue
            to_dt = from_dt.astimezone(data['to_tz'])
            to_date_str = to_dt.strftime(data['pattern'])
            oldpath = '{}{}'.format(data['src'], filename)
            newpath = '{}{}{}'.format(data['dst'], to_date_str, file_ext)
            validated_files.append((oldpath, newpath))
    
    if not validated_files:
        msgs.append('No files to prcess in source folder.')
        return msgs
    
    if not data['dry']:
        try:
            os.makedirs(data['dst'])
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
            
    for src, dst in validated_files:
        msgs.append('{} --> {}'.format(src, dst))
        if not data['dry']:
            shutil.copy2(src, dst)
            if data['mode'] == 'move' and data['from_tz'] != data['to_tz']:
                os.remove(src)

    return msgs    
   
    
def main(argv):
    data = dict(
        src='./',
        dst='./',
        from_tz='UTC',
        to_tz='UTC',
        mode='copy',
        pattern='%y%d%m%H%M%S',
        dry=False,
    )
    try:
        opts, args = getopt.getopt(
            argv,
            'hs:d:f:t:m:p:',
            [
                'help',
                'source-directory=',
                'destination-directory=',
                'from-tz=',
                'to-tz=',
                'mode=',
                'pattern=',
                'dry-run',
            ]
        )
    except getopt.GetoptError as e:
        print ('{}. Try --help switch fro help. Basic syntax is:'.format(e))
        print(help(True))
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(help())
            sys.exit()
        elif opt in ("-s", "--source-directory"):
            data['src'] = arg
        elif opt in ("-d", "--destination-directory"):
            data['dst'] = arg
        elif opt in ("-f", "--from-tz"):
            data['from_tz'] = arg
        elif opt in ("-t", "--to-tz"):
            data['to_tz'] = arg
        elif opt in ("-m", "--mode"):
            data['mode'] = arg
        elif opt in ("-p", "--pattern"):
            data['pattern'] = arg
        elif opt == "--dry-run":
            data['dry'] = True

    errors = validate(data)
    if errors:
        print(*errors, sep='\n')
        return
    result = run(data)
    print(*result, sep='\n')
    sys.exit()

if __name__ == "__main__":
    main(sys.argv[1:])
