


import zipfile
import sys
import os
import yaml 
import urllib
import json

# get configuration
y                       = yaml.load( open( 'configuration.yaml' , 'r' ) , Loader=yaml.FullLoader )
kuiper_update_log_file  = "Kuiper-update.log"
update_progress         = "Kuiper-update.progress"
release_url             = y['Git']['git_url_release']
kuiper_backup           = 'kuiper-backup.zip'
kuiper_update           = "Kuiper-update.zip"
kuiper_update_log       = open(kuiper_update_log_file , 'w')



backup_dirs_exclude     = [
    os.path.join( y['Directories']['artifacts_upload'][0] ,y['Directories']['artifacts_upload'][1] ) , 
    os.path.join( y['Directories']['artifacts_upload_raw'][0] ,y['Directories']['artifacts_upload_raw'][1] )
    ]
backup_files_exclude    = [
    kuiper_backup,
    kuiper_update_log_file,
    'gunicorn.pid',
    'Kuiper-install.log',
    kuiper_update,
    update_progress
]


# write the update progress to progress file
def write_progress( num , msg):
    fp = open(update_progress , 'w')
    fp.write(str(num) +":"+ msg )
    fp.close()



update_progress(1 , "Start update")

# print the kuiper update logs
def write_log(msg):
    # be quiet and dont print the messages if -q enabled
    if '-q' not in sys.argv:
        print msg
    kuiper_update_log.write(msg + "\n")



# rollback to the backup if updating failed
def rollback(kuiper_backup, backup_exclude_dirs , backup_exclude_files):
    update_progress(7 , "Start rollback to backup")

    try:
        write_log("Kuiper update: Start Rollback")
        for root, dirs, files in os.walk(y['Directories']['platform_folder']):  
            for file in files: 
                
                # exclude files in backup_files_exclude
                if file in backup_files_exclude:
                    continue

                file_path = os.path.join(root.lstrip("."), file)
                # if file in folders backup_dirs_exclude skip it
                if not file_path.startswith(tuple(backup_dirs_exclude)):
                    write_log( file_path )
                    os.remove(os.path.join(root, file))
        
        write_log("Kuiper update: removed all files")
        write_log("Kuiper update: start rollback old version files")

        zip_update = zipfile.ZipFile(kuiper_backup) 
        bUpdateSuccess = [True , "done"]
        for file in zip_update.namelist():
            
            # skip folders
            if file.endswith("/"):
                continue
            
            fileobj = zip_update.open(file)
            dst_path = file
            try:
                if os.path.dirname(dst_path) != "" and os.path.exists(os.path.dirname(dst_path)) == False:
                    os.makedirs(os.path.dirname(dst_path))
            except Exception as e:
                write_log( "Kuiper update: Failed to create folder ["+dst_path+"]" )
                bUpdateSuccess = [False , "Failed to create folder ["+dst_path+"] - " + str(e)]
                break


            try:
                dst_file = open(dst_path , 'wb')
                
                with dst_file as df:
                    df.write(fileobj.read())
                    write_log( "Kuiper update: update file ["+dst_path+"]") 
                    df.close()
            except Exception as e:
                write_log( "Kuiper update: couldn't update file ["+dst_path+"]")
                bUpdateSuccess = [False , "couldn't update file ["+dst_path+"]" + str(e)]
                break

        return bUpdateSuccess
    except Exception as e:
        write_log("Kuiper update: failed rollback - " + str(e))
        return [False , "failed rollback: " + str(e)]



            

# kuiper update function
def Update(kuiper_update , release_url , kuiper_backup , backup_exclude_dirs , backup_exclude_files):
    try:   
        
        # ====================== backup
        update_progress(2 , "Start backup")

        write_log( "Kuiper update: Start backup for kuiper " )
        # backup the current Kuiper files before updating it
        backup = zipfile.ZipFile(kuiper_backup , 'w')
        
        backup_files = []
        for root, dirs, files in os.walk(y['Directories']['platform_folder']):
            
            for file in files: 
                
                # exclude files in backup_files_exclude
                if file in backup_files_exclude:
                    continue

                file_path = os.path.join(root.lstrip("."), file)
                # if file in folders backup_dirs_exclude skip it
                if not file_path.startswith(tuple(backup_dirs_exclude)):
                    write_log( file_path )
                    backup_files.append( file_path )
                    backup.write(os.path.join(root, file))
        
        backup.close()
        
        # ===================== Get last release link 
        update_progress(3 , "Getting latest release info.")

        write_log("Kuiper update: getting latest release from GitHub ["+release_url+"] " )
        
        request = urllib.urlopen(release_url)
        response = request.read()
        data = json.loads(response)
        
        # Get download URL and download the 
        zip_url = data['zipball_url']
        write_log( "Start Downloading Kuiper " + data['tag_name'] )
        write_log( "GitHub URL zip file: " + zip_url )
        

        # ============== Download and Update Kuiper 
        update_progress(4 , "Start downloading latest release")
        # open the downloaded zip file from github
        urllib.urlretrieve(zip_url, "Kuiper-update.zip")

        update_progress(5 , "Start install updates")
        zip_update = zipfile.ZipFile(StringIO(zip_response).read()) 
        
        
        bUpdateSuccess = [True , "done"]
        for file in zip_update.namelist():
            
            # skip folders
            if file.endswith("/"):
                continue
            
            fileobj = zip_update.open(file)
            dst_path = "/".join( file.split("/")[1:] )
            try:
                if os.path.dirname(dst_path) != "" and os.path.exists(os.path.dirname(dst_path)) == False:
                    os.makedirs(os.path.dirname(dst_path))
            except Exception as e:
                write_log( "Kuiper update: Failed to create folder ["+dst_path+"]" )
                bUpdateSuccess = [False , "Failed to create folder ["+dst_path+"] - " + str(e)]
                break


            try:
                dst_file = open(dst_path , 'wb')
                
                with dst_file as df:
                    df.write(fileobj.read())
                    write_log( "Kuiper update: update file ["+dst_path+"]") 
                    df.close()
            except Exception as e:
                write_log( "Kuiper update: couldn't update file ["+dst_path+"]")
                bUpdateSuccess = [False , "couldn't update file ["+dst_path+"]" + str(e)]
                break

        return bUpdateSuccess
        
    except Exception as e:
        write_log( "Error downloading Kuiper update - check your Internet connection: " + str(e) )
        return [False , "Failed Kuiper update: " + str(e)]






# load the new update
up = Update(kuiper_update , release_url , kuiper_backup, backup_dirs_exclude , backup_files_exclude)
if up[0]:
    update_progress(6 , "New release installed")
    
else:
    # if failed rollback to the old backup
    rb = rollback(kuiper_backup, backup_dirs_exclude , backup_files_exclude)
    if rb[0]:
        write_log("Kuiper update: rollback done")
        update_progress(8 , "Update failed rollback done - check logs")
        print "False:" + up[1] + " - rollback done"
    else:
        write_log("Kuiper update: rollback failed - " + rb[1])
        update_progress(9 , "Update failed rollback failed - check logs")
        

# close the logging 
kuiper_update_log.close()

# restart gunicorn worker
#os.system("kill -HUP $(cat gunicorn.pid)")
