#!/usr/bin/env python3

import re
from pprint import pprint

"""
This script takes a file describing a toc and generates pdfmark directives that
generate a correct table of contents

Commandline Parameters:

        tox.py <tocfile> <outputfile> <page_offset> <splitfiles>

        page_offset
                offset of page numbers that should be added to all pagenumbers
        tocfile
                file containing toc specification
        outputfile
                file where the pdfmarks should be written to
        splitfiles
                maximum number of lines per pdfmark file
                when splitting files, the index of the first line in each file
                is appended to the original outputfile-name

The tocfile should look similar to:

1.      Chapter one     2
1.1     subchapter one  3
2.      blub            5
A.      Appendix        6
A.1     subapp          3

Note that the chapter numbers need to start at the beginning of each line and
the page number needs to be followed immediately by the newline.
In order to achieve correct nesting, chapter numbers of subchapters need to
be prefixed by the number of their parent.  Whitespace between the fields is
ignored. See the regexes in the function *tokenize* for reference.

Customizing
===========

Different toc-file format
        1. implement tokenizer (yields tuple(chapter, title, page) records)
        2. implement find_children function that, given a chapter number,
           searches through a list of records and returns all children of the
           given chapter.

Further Information
===================

pdftk
        In order to get rid of old bookmarks, filter the file through pdftk
        $ pdftk in.pdf cat output out.pdf

ghostscript
        The generated pdfmark file can be given to ghostscript as an inputfile:
        $ gs -sDEVICE=pdfwrite -sOutputFile=out.pdf in*.pdf pdfmark

pdfmark reference
        http://www.adobe.com/content/dam/Adobe/en/devnet/acrobat/pdfs/pdfmark_reference.pdf

"""


def tokenize(textfile):
        """
        Read from the given filename and process the toc file

        yields records of the form (chapter_number, title, page)
        """
        reg = re.compile(r"^((?:[A-Z]\.)?[0-9.]*)\s(.*)\s(\d+)$")
        alt = re.compile(r"^(.*)\s(\d+)$")
        with open(textfile) as f:
                prev_num = ''
                cnt = 1
                for line in f:
                        try:
                                result = re.match(reg, line).groups()
                                num,title,page = result
                                prev_num = num
                                cnt = 1
                        except Exception as e:
                                try:
                                        result = re.match(alt, line).groups()
                                        title,page = result
                                        num = "{}.{}".format(prev_num,cnt)
                                        cnt+=1
                                except Exception as e:
                                        print("Skipping toc line: %s"%line)
                                        continue
                        yield (num, title, page)

def apply_page_offset(records, offset=0):
        """
        Add the given offset to the page number of all records
        """
        for num,title,page in records:
                yield (num, title, int(page)+offset)

def get_matching_prfx(parent_rec, records):
        """
        Find children, using prefix matching of chapter numbers
        """
        num,title,page = parent_rec
        return [(n,t,p) for n,t,p in records if n.startswith(num)]

def check_title_length(maxlen, records):
        """
        Prints all titles that are longer than maxlen

        pdfmark /title fields have a maximum length of 256 bytes or 126 unicode
        chars. The recommended length is 32 characters. See the spec for
        details.
        """
        for num,title,page in records:
                if len(num)+len(title)+1 > maxlen:
                        print(num,title,page)

def check_duplicate_targets(records):
        """
        Calculate a histogram of pagenumbers and print all pages that have more
        than 1 reference
        """
        counts = {}
        for n,t,page in records:
                counts[page] = counts.get(page,0)+1
        pprint({k:v for k,v in counts.items() if v!=1})

def tree_ize(records, find_children=get_matching_prfx):
        """
        Builds a tree structure from a list of records.
        Uses the given function *find_children* to group records into a tree
        structure.

        input format: tuple(chapter_num, title, page)

        output format: 
                return [node0, node1, ...]
                node = (node_data, children)
                node_data = (chapter_num, title, page)
                children = (child_node0, child_node1, ...)
        """
        records = list(records)
        while True:
                try:
                        parent = records.pop(0)
                        children = find_children(parent, records)
                        for child in children:
                                records.remove(child)
                        yield (parent, tuple(tree_ize(children)))
                except IndexError as e:
                        return

def deep_len(tree):
        """
        Find the number of all descendants of the given node
        """
        return sum(1+deep_len(children) for data,children in tree)

def pdfmark_toc(tree):
        """
        Generate pdfmark instructions from the given toc tree representation

        See tree_ize for the tree format
        See pdfmark spec for the output language

        yields a list of strings, each containing a line of toc
        """
        for node in tree:
                data, children = node
                num,title,page = data
                if len(children) == 0:
                        yield "[/Title ({num}: {title}) /Page {page} /OUT pdfmark\n".format(
                                num=num,
                                title=title,
                                page=page)
                else:
                        yield "[/Count -{count} /Title ({num}: {title}) /Page {page} /OUT pdfmark\n".format(
                                count=len(children),
                                num=num,
                                title=title,
                                page=page)
                        yield from pdfmark_toc(children)

def splitfiles(l, n):
        """
        Split the list into several lists, each containing no more than n items
        """
        l = list(l)
        for i in range(0, len(l), n):
                yield (i, l[i:i+n])

                        

def wite_pdfmark_file(tree, outfile=None, chunksize=None):
        """
        Writes the given tree to the given outfile, optionally partitioning it
        into files of maximum chunksize lines

        If no outfile is given, nothing is done
        """
        if outfile is None:
                return
        lines = list(pdfmark_toc(tree))
        if chunksize is None:
                with open(outfile, "w") as f:
                        f.writelines(lines)
        else:
                for index,linechunk in splitfiles(lines, int(chunksize)):
                        with open(outfile+str(index), "w") as f:
                                f.writelines(linechunk)
        
def main(self, textfile, outfile=None, page_offset=0, chunksize=None):
        flat = list(apply_page_offset(tokenize(textfile), int(page_offset)))
        tree = tuple(tree_ize(flat))
        wite_pdfmark_file(tree, outfile, chunksize)
        pprint(tree)
        #check_title_length(64, flat)
        #check_duplicate_targets(flat)

if __name__=='__main__':
        import sys
        main(*sys.argv)
