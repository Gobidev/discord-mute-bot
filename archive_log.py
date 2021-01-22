import glob
import os.path


# Rename Bot.log to avoid large file sizes
if __name__ == '__main__':
    all_archive_files = glob.glob(os.path.join(os.getcwd(), "logs", "*.log.*"))
    current_max = int(all_archive_files[-1][-1])
    os.rename(os.path.join("logs", "Bot.log"), os.path.join("logs", "Bot.log.{0}".format(current_max + 1)))
