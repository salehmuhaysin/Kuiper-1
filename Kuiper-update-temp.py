import time 





def update_log(msg):
    f = open("Kuiper-update.log" , 'w+')
    f.write(msg+'\n')
    f.close()

def update_progress(msg):
    fp = open("Kuiper-update.progress" , 'w')
    fp.write(msg + "\n")
    fp.close()

update_log("start update")


update_progress("1:Start backup")
time.sleep(10)
update_progress("2:Download new release")
time.sleep(10)
if 5 < 10:
    update_progress("3:Start updating Kuiper")
    time.sleep(10)
    update_progress("4:New release installed")
else:
    update_progress("5:Start rollback to backup")
    time.sleep(10)
    update_progress("6:Update failed")

update_log('True:done update')



