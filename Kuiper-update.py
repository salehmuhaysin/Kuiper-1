


import zipfile
import sys
import os
import yaml 

# get configuration
y                       = yaml.load( open( 'configuration.yaml' , 'r' ) , Loader=yaml.FullLoader )
kuiper_update_log_file  = "Kuiper-update.log"
kuiper_update_log       = open(kuiper_update_log_file , 'w')
release_url             = y['Git']['git_url_release']
kuiper_backup           = 'kuiper-backup.zip'

backup_dirs_exclude     = [
    os.path.join( y['Directories']['artifacts_upload'][0] ,y['Directories']['artifacts_upload'][1] ) , 
    os.path.join( y['Directories']['artifacts_upload_raw'][0] ,y['Directories']['artifacts_upload_raw'][1] )
    ]
backup_files_exclude    = [
    kuiper_backup,
    kuiper_update_log_file
]






# print the kuiper update logs
def write_log(msg):
    # be quiet and dont print the messages if -q enabled
    if '-q' not in sys.argv:
        print msg
    kuiper_update_log.write(msg + "\n")



# rollback to the backup if updating failed
def rollback(kuiper_backup, backup_exclude_dirs , backup_exclude_files):
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
def Update(release_url , kuiper_backup , backup_exclude_dirs , backup_exclude_files):
    try:   
        # ===================== Get last release link 
        write_log("Kuiper update: getting latest release from GitHub ["+release_url+"] " )
        
        request = urllib.urlopen(release_url)
        response = request.read()
        data = json.loads(response)
        
        # Get download URL and download the 
        zip_url = data['zipball_url']
        write_log( "Start Downloading Kuiper " + data['tag_name'] )
        write_log( zip_url )
        zip_response = urllib.urlopen(zip_url)
        
        
        # ====================== backup
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
        
        # ============== Download and Update Kuiper 

        # open the downloaded zip file from github
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
up = Update(release_url , kuiper_backup, backup_dirs_exclude , backup_files_exclude)
if up[0]:
    print "True:Done Update"
else:
    # if failed rollback to the old backup
    rb = rollback(kuiper_backup, backup_dirs_exclude , backup_files_exclude)
    if rb[0]:
        write_log("Kuiper update: rollback done")
        print "False:" + up[1] + " - rollback done"
    else:
        write_log("Kuiper update: rollback failed - " + rb[1])
        print "False:" + up[1] + " - failed to role back"
        

# close the logging 
kuiper_update_log.close()

os.system("kill -HUP $(cat gunicorn.pid)")
