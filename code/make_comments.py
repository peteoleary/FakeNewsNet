from util.util import open_read_write_json_file
import sys

# "id": "politifact14856",
# "labels": 1,
# "content": "originally posted by opsspec1991 originally posted byconsidering all of the news thats coming out demonstrating all of the sexual accusations that show how the congressmen in washington conduct themselves, do you really feel that something like this about schumer couldnt be correct? i admit, ive jumped the gun on some posts and posted items that are questionable, but on my behalf i dont purposely do it out of spite, there does that make you happy.",
# "comments": [
    # {
        # "comment": "what about nancy pelosi i thought they skipped the meeting about tax reform to have a romantic day together  chucks a womanizer i guess"
    # },
    # {
        # "comment": "fake news"
    # }

def make_one_comment(item):
    return item

if __name__ == "__main__":
    open_read_write_json_file(sys.argv[1], "comments", make_one_comment)