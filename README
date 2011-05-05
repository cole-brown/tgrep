tgrep (PertGyp)
===============

Written by Cole Brown (spydez).
Designed for the 'reddit Backend Challenge'  (http://redd.it/fjgit).



The Short Version
-----------------
I passed the Backend Challenge, along with 15-30 others (~30 in total, but some
of those did the Frontend Challenge), but royally botched the phone interview.

Such is life.



The License
-----------

See LICENSE for legalese. The short version is it's BSD. BSD 3-clause.
Hack on it if you want and what have you.



The Disclaimer
--------------

- Developed and tested on OS X 10.6.6 in Python 2.6.1
- Works For Me (TM)
- Tested on a 233.2 KiB raldi's perl script log, and a 3.6 MiB and 6.7 GiB
  bash/python generated log (scripts/loggen.sh).
- In config.py, these really need to be configured properly. I've guessed the
  best I can, but...
  - LOG_LINE_BYTES - size of an average log line
  - A_GOOD_CHUNK_TO_READ
  - REFOCUS_FACTOR 
    - Not as important, though tweaking helps reel in the seek/reads a lot. 
- This is more Github Flavored Markdown than normal Markdown.
  - http://github.github.com/github-flavored-markdown/preview.html
  - Well, right now it's just text because it has Markdown errors 
    I'm leaving for now.


The Assumptions
---------------

tgrep assumes:

- A steady number of logs per second.
- Log lines are >500 bytes in size, and a newline is guaranteed to exist in a
  chunk of the file of size 1500 bytes. Adjust LOG_LINE_BYTES and
  MORE_THAN_ONE_LINE in config.py if this is false.
- How file ends was unspecified. tgrep assumes a log entry and then either
  exactly one newline or exactly zero.
- How file begins was unspecified. tgrep assumes it starts directly off with a
  log entry.
- A valid config file. No range or error checking is done.



The Big O
---------

tgrep runs in O(m log n) time. It may sound bad, but m is very small relative to
n (e.g. m = 600 KiB, n = 6.7 GiB (actual numbers from testing)). The 'log n' is
a time-adjusted binary search, which performs significantly better than a
"stupid" binary search (these can be compared in tgrep (see options)). The 'm'
is a linear search to find the exact bounds of the desired region in the log
after the binary search has gotten 'close enough'. In the worst case, tgrep must
run twice (see Special Cases), in which case it is... still O(m log n). In the
best case, n is 2 searches to eliminate 99.9% of the file, and m is a few KiB
for the rest.

### Actual Times

Note: These are for small regions, which are easier for TAB search to 
hone down on...

 - `tgrep 9:06 raldi.log --vv` on a 233 KiB file:
     -- statistics --
    seeks:        6
    reads:        8 (total)
    reads:        1 (just for printing)
    wide sweep loops:    3
    edge sweep loops:    2
    wide sweep time:  0:00:00.000913
    edge sweep time:  0:00:00.030429
    find  time:       0:00:00.038345
    print time:       0:00:00.000116
    total time:       0:00:00.038461
    log file size:    233.2 KiB

 - `tgrep 23:33 -v` on a 3.6 MiB file:
     -- statistics --
    seeks:        8
    reads:       10 (total)
    reads:        1 (just for printing)
    wide sweep loops:    5
    edge sweep loops:    2
    wide sweep time:  0:00:00.001025
    edge sweep time:  0:00:00.006998
    find  time:       0:00:00.014710
    print time:       0:00:00.000141
    total time:       0:00:00.014851
    log file size:    3.6 MiB   

 - `./tgrep --ee -c config-big.py 15:49:50` on a 6.7 GiB file:
     -- statistics --
    seeks:       14
    reads:       17 (total)
    reads:        2 (just for printing)
    wide sweep loops:    9
    edge sweep loops:    4
    wide sweep time:  0:00:00.062809
    edge sweep time:  0:00:00.107128
    find  time:       0:00:00.176845
    print time:       0:00:00.000211
    total time:       0:00:00.177056
    log file size:    6.7 GiB

   Note that I was testing. A lot. And I don't like rebooting... So these actual
   times are all with a 'hot' cache. That is, most of the file reads will
   probably hit a page in the processor cache; a page fault probably won't be
   generated and a hard drive probably usually won't be involved. So my wild
   guess is probably Wild.



Special Cases
-------------

### Slicing Log Right At Max In Early Stages

During the TAB search, neighbors of a line are not checked. It just peeks at a
timestamp and boogies. So in rare cases, it could slice down the max boundary to
/exactly/ the right position and not know it. The edge search knows this and
will act correctly in such cases.


### Time Region Is Only Partially In The File

If a file goes from Feb 12 06:30:00 to Feb 13 07:05:00, and the user requests
06:29-06:31:12, their search will return everything from the start of the file
to their end time. The same thing will happen if they're part way past the end
of the file.


### No Match

If there's no match, the user will get informed via syserr.


### *Two* Matching Regions

If a file goes from Feb 12 06:30:00 to Feb 13 07:05:00, and the user requests
06:50, well... did they want 06:50 from the 12th or 06:50 from the 13th? tgrep
will search the file twice and print both the 12th's and 13th's 6:50 region.


### Corrupted File

>.>
Yeah... don't search those.
<.<


### File Read Error

tgrep will quit.


### File Ending

How the log file ends was unspecified, so here is what tgrep will work with:

1. If a file ends with a newline, tgrep will work.
2. If a file ends without a newline, tgrep will work.
4. If TAB search guesses the match is too close to the end of the file (i.e.,
   past the last timestamp), tgrep will still work.

   - However, if the file ends with garbage or too much past that last
     timestamp... well, see 'Corrupted File' section.

### Large Files

tgrep works on files >4 GB in size. Yeah, should be obvious... but I'm a C++ guy
so I had to say it.


### File Names

On OS X (at least (it can also happen on VxWorks...)), files can have colons in
them. '02:03' is a valid filename. If, for some god-forsaken reason, you wanted
to search log '02:03' for a time range, tgrep will figure out that '02:03' is
your file and search in it.

Caveats: 
- You cannot search '02:03' for 02:03. You'll have to long-hand it to
  02:03-02:03:59.
- If '02:03' and '08:00' are both files. You cannot search '02:03' for 08:00 or
  vice versa. tgrep will notice they are both files and stop there.


### Time

tgrep uses Python's datetime module. It does not try to parse time itself. Doing
so may have shaved a fraction off of the run speed, but tgrep is IO bound, not
CPU bound, and trying to reimplement crufty stuff like time will get you into a
world of hurt:

- What about crossing day or month borders?
- What about leap years?
- etc.

Using a well used, well tested library avoids this sort of stuff.

That being said, tgrep is pretty rigid about the timestamp format the log
uses. It must be abbreviated month followed by day followed by HH:MM:SS. One or
more spaces in between. No exceptions.

### Out of order entries

The challenge said:

> The timestamps are always increasing -- we never accidentally put "Feb 1
  6:42:17" after "Feb 1 6:42:18".

But it was later revealed that:

> In very rare cases, they could be every so slightly out of order, but not
  enough to make a difference in practice.

tgrep was made with the challenge's assumption: monotonically increasing
timestamps. That said, this is untested but should be the case:

  - An out-of-order line at the beginning of a requested region will be caught.
  - An out-of-order line at the end of a requested region probably won't be
    caught.
  - Any out-of-order stuff going on inside a region is fine by tgrep.

tgrep doesn't sort, so your out-of-order lines will still be in the wrong place.



The Algorithmic Flow
--------------------

This is the 'happy day scenario'.


1. Input args and params are validated.


2. File is opened. File size, and first and last log timestamps are determined.


3. Input time is parsed into usable format. Time is then checked against the
   file. Is in even in the file? Is it in there twice? etc.


4. wide_sweep is called - a fast and pessimistic search function.

   wide_sweep makes no initial assumptions about the requested time range's
   location in the log. It starts off with the lower and upper bounds of its
   search set to the high and low timestamp/location of the log file. It then
   refines this. 

   1. A guess for the location of one of the requested times is made.

   2. That location is visited in the file, a small chunk is read, and one
      timestamp is extracted.

   3. This timestamp is compared against our upper and lower bounds. If it is
      better, it is used as the new bound. If it is worse, it is discarded and a
      'bad guess' is recorded.

   4. wide_sweep loops back to make another guess. It toggles between guessing
      for the higher and lower of the requested times.

   5. If a 'bad guess' has been marked against, say, the high bounds, then the
      high guess will be refocused away from the guessing function's focal point
      and forwards towards the end of the file from that point onwards.

   6. When the refocused guess also fails, that bound quits being checked and
      only the other is worked with.

   7. Once wide_sweep cannot guess any closer (or it has gotten 'close enough'
      (as determined in config file), it returns the bounds.


5. edge_sweep is called with the bounds determined by wide_sweep.

   edge_sweep is optimistic. It is built on the assumption that the bounds are
   now close. It reads in larger chunks of the file and linearly searches
   through them, checking every timestamp encountered.

   1. One of the bounds' location (higher or lower) is visited in the file. If
      the boundary is the higher bound, the location visited is actually the higher
      bound's position minus the chunk size intended to be read, so as to read 
      *up to* the higher boundary location.

   2. A chunk of the file is read; the chunk is much larger than that read
      during the wide_sweep phase.

   3. The entire chunk is searched for the edge of the boundary between
      not-in-the-requested-region and in-the-requested-region.

   4. If the edge is found, it is saved and the fact that it is found
      recorded. Otherwise the closest timestamp to it is saved as the new bound.

   5. If both edges are not found, edge_sweep loops back for another
      pass. edge_sweep will not search for edges it has already found.

   6. Once both edges of the requested region are found in the log, edge_sweep
      returns.


6. print_log_lines is called with the region bounds determined by edge_sweep.

   1. It seeks to the lower bound.

   2. A chunk is read; the chunk size is usually the same as the one used during
      the edge_sweep, unless the config file has been changed or the print function
      is near the end of the region.

   3. The chunk is printed to stdout.

   4. print_log_lines loops until the entire requested region of logs has been
      printed. It only reads in the amount of bytes in the region - no more.


7. A possible kink.

   Depending on the input time and the log file, there may be two regions in the
   file that match the request (See Special Cases section for details). If this
   is the case:
   
   1. Print a seperator if one is requested.
   
   2. Loop back to the beginning and redo everything for the second set of
      request times.


8. Statistics are printed if a statistics option is supplied.


9. tgrep is done.


### Flow 4.1 - Time-Adjusted Binary (TAB) Search

Boring old binary search is possible using tgrep. See the options section for
details. However the time-adjust binary search function, time_search_guess, is
much faster at finding an acceptable range for edge_sweep.

It's much faster for finding the boundaries in a fixed logs-per-second simulated
log file, anyways. And it seems like it will work better on Real Actual Logs
with peaks and valleys, however it's not been tested.

TAB works by using the starting and ending bytes and times of the file, and
calculating a bytes per second from that. It then uses this and the time between
the current best lower bounds and the requested lower bounds to estimate the
lower bound's position in the file. Similarly for the higher bound.


### Flow 4.5 - Refocusing Search

When wide_sweep has a bad guess during a loop, further guesses for that time
(whether it be the lower or upper bound) will be refocused. The REFOCUS_FACTOR
in the config file determines by how much. The refocusing factor moves the focal
point of the guess away from the original location and towards the lower or
upper bound (depending on which bound is currently being searched for). A
refocus factor of 0.15 moves the focus down 15% when searching for the lower
bound or up 15% when searching for the upper bound.

This 'refocusing' happens so that a search guess that is unusable for narrowing
the high and low bounds down to the requested region does not prematurely end
wide_sweep and leave edge_sweep with too much to search through.


### Flow 4.7 - Close Enough

For the wide_sweep, 'close enough' is defined in the config file by
WIDE_SWEEP_CLOSE_ENOUGH. If properly configured in relation to the
EDGE_SWEEP_CHUNK_SIZE, it could save several search/seek/read loops of
wide_sweep.



Possible Improvements
---------------------

- Start the search off with assumptions about the location of the requested logs
  (Flow 4). This could possibly cut out 2 or 4 reads (the small ones done during
  wide_sweep), so it's not a very substantial gain.

- Do statistical analysis on files to see where time X generally occurs. Use
  that in search instead of assuming a flat bytes per second rate of data
  generation.

- Know when the peek and valley times are. Build that knowledge into a
  function. Use that to improve search guessing.

- Sometimes two different sections of a log will match a supplied time
  range. For example, the log file goes from Feb 12 06:30 to Feb 13 07:00, and
  the user asks for logs with timestamp 6:50. That's in both the Feb 12 and Feb
  13 parts of the file. tgrep will find and print both linearly. This could be
  sped up if tgrep was designed to fork and search for each region at the same
  time.

- Provide ability to specify day in command arg (e.g. `tgrep "Feb 13 06:50"`)
  so that tgrep won't search and find both 06:50 logs if 06:50 exists twice 
  in the log.

- Patch HAProxy to spit out an index file of lines of timestamp with log file
  location, like:

    Feb 12 07:06:43 42949672960
    Feb 12 07:06:47 42949673123
    Feb 12 07:07:00 42949673399
    ...

  Then have tgrep search that for the right parts of the log file to print out.



Usage and Options
-----------------

    Usage: tgrep times
       Or: tgrep times [file]
       Or: tgrep times [options] [file]
       Or: tgrep [options] times [file]
       Or: tgrep [options] [file] [options] times [options]
       ...I don't really care; do whatever you want. Just gimme my times.
    
    Example:
       $ tgrep 8:42:04
         [log lines with that precise timestamp]
       $ tgrep 10:01
         [log lines with timestamps between 10:01:00 and 10:01:59]
       $ tgrep 23:59-0:03
         [log lines between 23:59:00 and 0:03:59]
       $ tgrep 23:59:30-0:03:01
         [log lines between 23:59:30 and 0:03:01
    
    Options:
      -h, --help            show this help message and exit
      -b, --binary          use pure binary search instead of time-adjusted binary
                            search
      -c CONFIG, --configfile=CONFIG
                            config file to use
      -e, --verbose-to-stderr
                            print statistics to stderr at end of run
      --ee                  print all statistics to stderr at end of run
      -v, --verbose         print statistics to stdout at end of run (-e
                            supercedes)
      --vv                  print all statistics to stdout at end of run (-e or
                            --ee supercedes)

###Time-Adjusted Binary Search vs Normal Binary Search

To compare tgrep's time-adjusted binary search against a normal binary search,
enable statistics with -v (for stdout) or -e (for stderr) and toggle the -b
option.

    $ ./tgrep 23:33:11 -e >/dev/null && ./tgrep 23:33:11 -e -b >/dev/null
    
     -- statistics --
    seeks:        5
    reads:        7 (total)
    reads:        1 (just for printing)
    wide sweep loops:    2
    edge sweep loops:    2
    wide sweep time:  0:00:00.000379
    edge sweep time:  0:00:00.007245
    find  time:       0:00:00.015521
    print time:       0:00:00.000013
    total time:       0:00:00.015534
    log file size:    3.6 MiB
    
     -- statistics --
    seeks:       12
    reads:       14 (total)
    reads:        1 (just for printing)
    wide sweep loops:    9
    edge sweep loops:    2
    wide sweep time:  0:00:00.001347
    edge sweep time:  0:00:00.007087
    find  time:       0:00:00.015351
    print time:       0:00:00.000014
    total time:       0:00:00.015365
    log file size:    3.6 MiB



Fragilities
-----------

- Corrupted files are not handled.
- File read errors cause tgrep to just quit. It will not try to re-read or
  reopen the file, or otherwise save its work. Any progress towards the answer
  is lost and tgrep starts over at the beginning next time.
- Config file is not error checked, range checked or idiot proofed.



TL;DR
-----

Run `tgrep <times> [log file]`.

If you want statistics, run `tgrep -v <times> [log file]`

If you want to play with config params, copy config.py and run
`tgrep -c <new config> <times> [log file]`


