#!/usr/bin/python
import MySQLdb
import cmd

db = MySQLdb.connect(host="localhost", # your host, usually localhost
                     user="root", # your username
                      passwd="fella", # your password
                      db="testdb") # name of the data base


class sqlcntrl(cmd.Cmd):
    """Simple command processor example."""

    def default(self, line):
        print 'd'
        cur = db.cursor() 
        cur.execute("%s" % (line,))
        for row in cur.fetchall() :
            print row
    
    def do_sql(self, line):
        cur = db.cursor() 
        cur.execute("%s" % (line,))
        for row in cur.fetchall() :
            print row[0]
    
    def do_EOF(self, line):
        return True

if __name__ == '__main__':
    sqlcntrl().cmdloop()
