## Monitoring Tomcat from python: a set of examples and explanations

### Quick start for experienced users

_Disclaimer: It's normal at a point like this to exhort people to use virtualenv; to fork the repo and clone that; and that sort of thing. Well, I'm not. "We're all adults here", right? This is a quick start. What follows is the bare minimum._

Clone this repo.

If you do not already have them, make sure you have Python 2.6+, [Requests](http://docs.python-requests.org/en/latest/), and [BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/) installed.

Determine the servername you want to hit. Formulate it to be complete from protocol to port (if not port 80), e.g. "http://big.damnserver.org:8080"

Determine the username and password by inspecting the target server's `conf/tomcat-users.xml` file and identifying the user account with the **"manager-script" role.**

From your repo's root directory, at the commandline, enter 

    `python run_monitors.py <servername> <username> <password>`

Compare the result to the code. You should be able to grasp what's going on.

### Explanations and background

#### overview: web apps in servlet containers

Monitoring and control/recovery for Java Servlet Container-based web apps is a problem of nested functionality, logic, and access.

![diagram of nested elements in problem space](/images/monitoring_problem_space.png)

At the outermost level is **the server, its OS, its network resources, and usually some kind of external data store.** Most monitoring devices or frameworks can access these pretty well. They can obtain statistics, run diagnostics, and execute recovery measures up to and including hard restarts, depending on permissions and non-extraordinary physical access. We can generally treat this as a solved problem.

The second layer in is **the JVM**. This is a bit more problematic; the JVM is, by design, a sandbox with strictly controlled interactions with the host system. JVM statistics, diagnostics, and control are exercised from within the JVM; you need a Java program to run those operations.

The third layer in is the **Tomcat server/servlet container itself.** It is a Java application, which can self-report all kinds of things.

Finally, the **web app hosted by Tomcat** is a Java app that, again, needs to self-report. Tomcat can give information on the Tomcat-level resources being used by the app, but the application's internal logic is opaque to Tomcat.

#### how this works with that: lowest common denomitator is damn common.

This repo contains examples of, and description of techniques for, handling the second and third layers in a non-invasive, low-effort fashion. It works by taking advantage of Tomcat's built-in Manager application:

 - Becuase it's a web app that ships with Tomcat, it works externally without need for additional installation. You only need to have the necessary permissions.

 - Because it's internal to the JVM, it can provide a pretty good information set about status, and resource usage, for the JVM at large and Tomcat in particular.

 - It does NOT provide any information that depends on the internal logic of the application.

Is the Tomcat Manager the best tool for the job? Well, no, not in absolute quality and usability. It does have big gaps in its rather rudimentary service interface, if such it can be called. There are better things than Tomcat Manager out there. But, Tomcat Manager is **built in**, and **100% HTTP**; so it does not require deployment of additional exotica such as JMX agents or additional Tomcat apps (such as the excellent [PSI Probe](https://code.google.com/p/psi-probe/), so using it doesn't demand going down any rabbit holes.

Look. This is intended to provide a _minimal_, and _minimally adequate_, Tomcat monitoring capability - _at minimal cost and effort_. Given those constraints, Tomcat Manager is still best of breed. 

#### Tomcat Manager

The Tomcat server exposes a number of interfaces for monitoring and control via the [Tomcat Manager](http://tomcat.apache.org/tomcat-7.0-doc/manager-howto.html). In a lot of ways, this is excellent. It permits users with proper authorization to deploy, run, shut down, reload, and restart Tomcat applications. It also provides the ability to monitor a lot of the otherwise difficult-to-access internal statistics of apps running in the Tomcat container, and the container itself.

The Tomcat Manager is a web application that ships with Tomcat. (See the docs for how to configure it for use.) The Tomcat Manager can be used in the following ways:

 - Via the web pages built into the app.

 - Via the Text Interface, a simplistic set of web services provided mainly for scripting support.

 - Via predefined Ant commands.

 - Via JMX controls.

Of these, the simplest way to support general monitoring and automated recovery is the Text Interface. The web pages are designed for humans; Ant is a specialty item; and JMX is rapidly falling out of favor due to its problematic security characteristics. (It's not unlikely that your internal network's administrators will block JMX traffic as a matter of policy.) 

There is one odd and brutal glitch here, though. The Text Interface provides full control over deploying, starting, stopping, etc; but it's strangely scanty on monitoring. This is probably an artifact of development history, rather than an intentional move on the part of the Tomcat team. Still, it sucks, and it makes a curious hybrid approach necessary: 

 - Text Interface for everything that it _does_ support, and 

 - Screen scraping the `/manager/status` web page that contains the monitoring info that the Text Interface will not provide.

This repo contains examples of doing this in Python. The examples try to be as simple and straightforward as possible. The current incarnation uses `requests` for HTTP client work, and `BeautifulSoup` for the screen scraping.

### Monitored statistics: Text Interface

The following information is available via the text interface (`<server>/manager/text/`):

#### Text Service: OS and JVM characteristics
URL: `<server>/manager/text/serverinfo`

This includes Tomcat version, JVM version and vendor, OS version, hostname, IP address

#### Text Service: Running Tomcat processes, by context path
URL: `<server>/manager/text/list`

For each process, lists:
 - Context Path
 - Version
 - Display Name
 - Running yes/no
 - How many user sessions

#### Text Service: JNDI Resources
URL: `<server>/manager/text/resources`

For each resource, lists JNDI name


### Monitored Statistics: scraped from status page
URL: `<server>/manager/status`

#### JVM Memory usage
This is a valuable piece of information to have: even if you don't know what these memory pools are, it's good to be able to know when they are running up against their limits.

For each pool, the page provides:
 - Memory Pool Name
 - Memory Type (heap/non-heap)
 - Initial Size
 - Total Size
 - Maximum Size
 - Currently Used (size and percentage)

The ordinary JVM memory pools are:
 - **CMS Old Gen:** The largest memory pool which should keep the long living objects. Objects are copied into this pool once they leave the survivor spaces.
 - **Par Eden Space:** The pool from which memory is initially allocated for most objects.
 - **Par Survivor Space:** The pool containing objects that have survived the garbage collection of the Eden space.
 - **CMS Perm Gen:** The pool containing all the reflective data of the virtual machine itself, such as class and method objects. With Java VMs that use class data sharing, this generation is divided into read-only and read-write areas.
 - **Code cache:** The HotSpot Java VM also includes a code cache, containing memory that is used for compilation and storage of native code.

References and content sources:
 - [stackoverflow: How is the java memory pool divided?](http://stackoverflow.com/questions/1262328/how-is-the-java-memory-pool-divided)
 - [A short Primer to Java Memory Pool Sizing and Garbage Collectors](http://www.scalingbits.com/javaprimer)
 - [Java Garbage Collection Distilled](http://www.infoq.com/articles/Java_Garbage_Collection_Distilled)


#### Connector session threads
Connectors for various protocols (HTTP, HTTPS, AJP, etc.) show some of the most important information for determining the state of an application. The Tomcat Manager provides a rich set of data.

For each thread associated with a connector, the Tomcat Manager tells us:
 - Stage: the part of the job cycle in which the thread currently resides.
   - S: Service (thread is busy satisfying a request)
   - F: Finishing (thread is done with work and is releasing resources)
   - R: Ready (thread is idle, awaiting assignment to a request)
   - K: Keepalive (thread is being used by a connection that is being held open even when there is no immediate work)
 - Time: the length of time in ms that the thread has been in this stage. Long times, especially when associated with a lack of activity, can indicate an orphaned or stuck thread.
 - Bytes Sent
 - Bytes Received
 - Client (Forwarded)
 - Client (Actual)
 - VHost
 - Request
