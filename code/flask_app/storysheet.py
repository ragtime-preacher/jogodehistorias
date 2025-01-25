# a file for holding functions to interact with our storysheet.

# Stolen from ChatGPT
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# define the scope
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]

# authenticate using the service account JSON key

creds = ServiceAccountCredentials.from_json_keyfile_name("/home/lurch5-64/progamming/jogodehistorias/creds/jogodehistorias-beta-e6e6f9107f08.json", scope)
"""client = gspread.authorize(creds)

# open the google sheet
sheet = client.open("rigmarole-testing").worksheet("stories")

# read data from the sheet
data = sheet.get_all_records ()
print ("sheet data:", data)
"""
"""# write data to the sheet
sheet.update_cell(2, 1, "Hello, Google Sheets!") # update cell B2

# add a new row
sheet.append_row(["New Data", "123", "456"])
"""
class StorySheet :
    def __init__ (
            self,
            creds: ServiceAccountCredentials,
            workbook_name: str,
            worksheet_name: str
        ):
        self.client = gspread.authorize(creds)
        self.workbook = self.client.open(workbook_name)
        self.worksheet = self.workbook.worksheet(worksheet_name)
        try:
            self.metasheet = self.workbook.worksheet("meta")
        except gspread.WorksheetNotFound:
            self.metasheet = self.workbook.add_worksheet (title="meta")
        
        # self.clean_slate()
        self.data = self.worksheet.get_all_records()

    def update_data (self) :
        self.data = self.worksheet.get_all_records()
        return self.data
    
    def get_next_storyid (self) :
        highest_storyid = -1
        for row in self.data :
            if row ["storyid"] > highest_storyid:
                highest_storyid = row["storyid"]
        return highest_storyid + 1
    
    def add_new_round_header (self) :
        existing_headers = self.worksheet.row_values(1)
        furthest_story = 0
        for i_header in existing_headers:
            if "round" not in i_header:
                continue
            if int(i_header.split("round")[1]) > furthest_story:
                furthest_story = int(i_header.split("round")[1])
        existing_headers.append(f"round{furthest_story+1}")
        self.worksheet.update(range_name='1:1', values=[existing_headers])
        self.update_data ()

    def add_new_user (self, username: str) :
        self.worksheet.append_row([f"{self.get_next_storyid()}", username])
        # with every new user, we should add another round column
        self.add_new_round_header ()
        # ^ this function takes care of StorySheet.update_data()

    def clean_slate (self) :
        # Delete everything from the sheet
        self.worksheet.delete_rows(1, len(self.worksheet.col_values(1)))
        # replace the important headers (storyid and username)
        self.worksheet.append_row(["storyid", "username"])
        self.update_data ()
        # We'd also better clear out the meta sheet
        self.metasheet.delete_rows(1, len(self.metasheet.col_values(1)))
        self.metasheet.append_row(["room_id", "game_started", "owner"])

    def count_players (self) :
        self.update_data()
        return len(self.data)

    def insert_room_id (self, room_id) :
        self.metasheet.update_cell(2, 1, room_id)

    def set_game_started (self, accept: bool) :
        self.metasheet.update_cell(2, 2, accept)

    def set_owner (self, owner: str) :
        self.metasheet.update_cell(2, 3, owner)

    def get_metadata (self) :
        return self.metasheet.get_all_records()[0]

    def get_current_story (self, storyid: int) -> str :
        total_story = ""
        self.update_data()
        try:
            story_row = self.data[storyid]
        except IndexError as ie:
            return str(ie)
        assert (type(story_row) == dict)
        for i_key in story_row:
            # so the only cells that we'll process here are the cells that have
            #   "round" in the key - that is to say, only the cells that
            #   contain parts of the story.
            if not "round" in i_key:
                continue
            # and now we'll check to see if the story is empty (hasn't 
            #   been written yet)
            if story_row[i_key] == "" :
                continue
            # Assim, the we'll only add the next part of the story if there's
            #   actually something to add. "" is skipped.
            total_story += f"{story_row[i_key]}\n"
        # If we've gotten this far, the total_story variable will be either
        #   a string composed of various concatenated sub-strings or an empty
        #   string "". If it's a "", that means that none of the story has been
        #   written yet and this is the first round. We'll change total_story
        #   to be some kind of "first round - start writing message".
        if total_story == "" :
            return "Nothing yet. Start writing! \"Once upon a time...\""
        else:
            return str (total_story)
    
    # get_target_storyid
    #   given a username, establish what story we should be working on next.
    #   we'll do this by counting how many sections of the story have been
    #   written already (how many rounds are filled).
    def get_target_storyid (self, username: str) -> int:
        self.update_data ()
        for row in self.data:
            assert type(row) == dict
            if row["username"] == username:
                # we've found the home row!
                home_storyid = row["storyid"]
                # now... how many rounds have been written?
                rounds_written_counter = 0
                for i_col_header in row.keys():
                    if "round" not in i_col_header:
                        # this isn't one of the round columns
                        continue
                    else:
                        if row[i_col_header] != "":
                            # We'll assume that there's something written here
                            rounds_written_counter += 1
                            continue
                        elif row[i_col_header] == "":
                            """
We've found an empty column. This means that someone'll be writing here next round.
it also means that we've counted the right number of stories to jump down in
    our order to find the next target story. The only thing that remains is to
    use (rounds_written_counter + home_storyid) % total_users
    to give us a valid storyid to use as a target. 
We should be able to get total_users by computing the length of
    StorySheet.data."""
                            total_users = len(self.data)
                            return (int(home_storyid) \
                                    + rounds_written_counter) \
                                        % total_users
        return 0
    # this return should never be used.


def main () :
    testSheet = StorySheet(creds, "rigmarole-testing", "stories")
    testSheet.clean_slate()
    testSheet.add_new_user("Burt")
    testSheet.add_new_user("tom")
    testSheet.add_new_user("William")

if __name__ == "__main__":
    main ()