# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.


""" Bibcirculation web interface """

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

# others invenio imports
from invenio.config import CFG_SITE_LANG, \
                           CFG_SITE_URL, \
                           CFG_SITE_SECURE_URL, \
                           CFG_ACCESS_CONTROL_LEVEL_SITE, \
                           CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS


from invenio.webuser import getUid, page_not_authorized, isGuestUser, \
                            collect_user_info
from invenio.webpage import page, pageheaderonly, pagefooteronly
from invenio.search_engine import create_navtrail_links, \
     guess_primary_collection_of_a_record, \
     get_colID, check_user_can_view_record
from invenio.urlutils import redirect_to_url, \
                             make_canonical_urlargd
from invenio.messages import gettext_set_language
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.websearchadminlib import get_detailed_page_tabs
from invenio.access_control_config import VIEWRESTRCOLL
from invenio.access_control_mailcookie import mail_cookie_create_authorize_action
import invenio.template
webstyle_templates = invenio.template.load('webstyle')
websearch_templates = invenio.template.load('websearch')

# bibcirculation imports
bibcirculation_templates = invenio.template.load('bibcirculation')
from invenio.bibcirculation import perform_new_loan_request, \
                                   perform_new_loan_request_send, \
                                   perform_get_holdings_information, \
                                   perform_borrower_loans, \
                                   perform_loanshistoricaloverview

class WebInterfaceYourLoansPages(WebInterfaceDirectory):
    """Defines the set of /yourloans pages."""


    _exports = ['', 'display', 'loanshistoricaloverview']

    def index(self, req, form):
        """ The function called by default
        """
        redirect_to_url(req, "%s/yourloans/display?%s" % (CFG_SITE_URL, req.args))

    def display(self, req, form):
        """
        Displays all loans of a given user
        @param ln:  language
        @return the page for inbox
        """
        argd = wash_urlargd(form, {'barcode': (str, ""),
                                   'borrower': (int, 0)})


        # Check if user is logged
        uid = getUid(req)
        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/yourloans/display" % \
                                             (CFG_SITE_URL,),
                                       navmenuid="yourloans")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/yourloans/display%s" % (
                        CFG_SITE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        _ = gettext_set_language(argd['ln'])




        body = perform_borrower_loans(uid=uid,
                                      barcode=argd['barcode'],
                                      borrower=argd['borrower'],
                                      ln=argd['ln'])

        return page(title       = _("Your Loans"),
                    body        = body,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    navmenuid   = "yourloans")

    def loanshistoricaloverview(self, req, form):
        """

        """

        argd = wash_urlargd(form, {})

        # Check if user is logged
        uid = getUid(req)
        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/yourloans/loanshistoricaloverview" % \
                                             (CFG_SITE_URL,),
                                       navmenuid="yourloans")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/yourloans/loanshistoricaloverview%s" % (
                        CFG_SITE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        _ = gettext_set_language(argd['ln'])

        body = perform_loanshistoricaloverview(uid=uid,
                                               ln=argd['ln'])

        return page(title       = _("Loans - historical overview"),
                    body        = body,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = argd['ln'],
                    navmenuid   = "yourloans")


class WebInterfaceHoldingsPages(WebInterfaceDirectory):
    """Defines the set of /holdings pages."""

    _exports = ['', 'display', 'request', 'send']

    def __init__(self, recid=-1):
        self.recid = recid


    def index(self, req, form):
        """
        Redirects to display function
        """
        return self.display(req, form)

    def display(self, req, form):
        """

        """

        argd = wash_urlargd(form, {'do': (str, "od"),
                                   'ds': (str, "all"),
                                   'nb': (int, 100),
                                   'p': (int, 1),
                                   'voted': (int, -1),
                                   'reported': (int, -1),
                                   })


        body = perform_get_holdings_information(self.recid, argd['ln'])

        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)


        user_info = collect_user_info(req)
        (auth_code, auth_msg) = check_user_can_view_record(user_info, self.recid)
        if auth_code and user_info['email'] == 'guest' and not user_info['apache_user']:
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            target = '/youraccount/login' + \
                make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : \
                CFG_SITE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target)
        elif auth_code:
            return page_not_authorized(req, "../", \
                text = auth_msg)


        unordered_tabs = get_detailed_page_tabs(get_colID(guess_primary_collection_of_a_record(self.recid)),
                                                    self.recid,
                                                    ln=argd['ln'])
        ordered_tabs_id = [(tab_id, values['order']) for (tab_id, values) in unordered_tabs.iteritems()]
        ordered_tabs_id.sort(lambda x, y: cmp(x[1], y[1]))
        link_ln = ''
        if argd['ln'] != CFG_SITE_LANG:
            link_ln = '?ln=%s' % argd['ln']
        tabs = [(unordered_tabs[tab_id]['label'], \
                 '%s/record/%s/%s%s' % (CFG_SITE_URL, self.recid, tab_id, link_ln), \
                 tab_id in ['holdings'],
                 unordered_tabs[tab_id]['enabled']) \
                for (tab_id, order) in ordered_tabs_id
                if unordered_tabs[tab_id]['visible'] == True]
        top = webstyle_templates.detailed_record_container_top(self.recid,
                                                               tabs,
                                                               argd['ln'])
        bottom = webstyle_templates.detailed_record_container_bottom(self.recid,
                                                                     tabs,
                                                                     argd['ln'])

        title, description, keywords = websearch_templates.tmpl_record_page_header_content(req, self.recid, argd['ln'])
        navtrail = create_navtrail_links(cc=guess_primary_collection_of_a_record(self.recid), ln=argd['ln'])
        navtrail += ' &gt; <a class="navtrail" href="%s/record/%s?ln=%s">'% (CFG_SITE_URL, self.recid, argd['ln'])
        navtrail += title
        navtrail += '</a>'

        return pageheaderonly(title=title,
                              navtrail=navtrail,
                              uid=uid,
                              verbose=1,
                              req=req,
                              language=argd['ln'],
                              navmenuid='search',
                              navtrail_append_title_p=0) + \
                              websearch_templates.tmpl_search_pagestart(argd['ln']) + \
                              top + body + bottom + \
                              websearch_templates.tmpl_search_pageend(argd['ln']) + \
                              pagefooteronly(lastupdated=__lastupdated__, language=argd['ln'], req=req)

    # Return the same page wether we ask for /record/123 or /record/123/
    __call__ = index


    def request(self, req, form):
        """

        """

        #raise repr(form)
        # Copy of webcomment

        argd = wash_urlargd(form, {'due_date': (str, ""),
                                   'barcode': (str, ""),
                                   'from_year': (int, 0),
                                   'from_month': (int, 0),
                                   'from_day': (int, 0),
                                   'to_year': (int, 0),
                                   'to_month': (int, 0),
                                   'to_day': (int, 0),
                                   })
        uid = getUid(req)

        #due_date=argd['due_date'],

       # raise repr(form)

        body = perform_new_loan_request(recid=self.recid,
                                        uid=uid,
                                        due_date=argd['due_date'],
                                        barcode=argd['barcode'],
                                        from_year=argd['from_year'],
                                        from_month=argd['from_month'],
                                        from_day=argd['from_day'],
                                        to_year=argd['to_year'],
                                        to_month=argd['to_month'],
                                        to_day=argd['to_day'],
                                        ln=argd['ln'])


        _ = gettext_set_language(argd['ln'])

        #"""
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../holdings/request",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/record/%s/holdings/request%s" % (
                        CFG_SITE_URL,
                        self.recid,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        #"""



        user_info = collect_user_info(req)
        (auth_code, auth_msg) = check_user_can_view_record(user_info, self.recid)
        if auth_code and user_info['email'] == 'guest' and not user_info['apache_user']:
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            target = '/youraccount/login' + \
                     make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : \
                CFG_SITE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target)
        elif auth_code:
            return page_not_authorized(req, "../", \
                text = auth_msg)



        unordered_tabs = get_detailed_page_tabs(get_colID(guess_primary_collection_of_a_record(self.recid)),
                                                    self.recid,
                                                    ln=argd['ln'])
        ordered_tabs_id = [(tab_id, values['order']) for (tab_id, values) in unordered_tabs.iteritems()]
        ordered_tabs_id.sort(lambda x, y: cmp(x[1], y[1]))
        link_ln = ''
        if argd['ln'] != CFG_SITE_LANG:
            link_ln = '?ln=%s' % argd['ln']
        tabs = [(unordered_tabs[tab_id]['label'], \
                 '%s/record/%s/%s%s' % (CFG_SITE_URL, self.recid, tab_id, link_ln), \
                 tab_id in ['holdings'],
                 unordered_tabs[tab_id]['enabled']) \
                for (tab_id, order) in ordered_tabs_id
                if unordered_tabs[tab_id]['visible'] == True]
        top = webstyle_templates.detailed_record_container_top(self.recid,
                                                               tabs,
                                                               argd['ln'])
        bottom = webstyle_templates.detailed_record_container_bottom(self.recid,
                                                                     tabs,
                                                                     argd['ln'])

        title, description, keywords = websearch_templates.tmpl_record_page_header_content(req, self.recid, argd['ln'])
        navtrail = create_navtrail_links(cc=guess_primary_collection_of_a_record(self.recid), ln=argd['ln'])
        navtrail += ' &gt; <a class="navtrail" href="%s/record/%s?ln=%s">'% (CFG_SITE_URL, self.recid, argd['ln'])
        navtrail += title
        navtrail += '</a>'

        return pageheaderonly(title=title,
                              navtrail=navtrail,
                              uid=uid,
                              verbose=1,
                              req=req,
                              language=argd['ln'],
                              navmenuid='search',
                              navtrail_append_title_p=0) + \
                              websearch_templates.tmpl_search_pagestart(argd['ln']) + \
                              top + body + bottom + \
                              websearch_templates.tmpl_search_pageend(argd['ln']) + \
                              pagefooteronly(lastupdated=__lastupdated__, language=argd['ln'], req=req)




    def send(self, req, form):
        """

        """

        argd = wash_urlargd(form, {'barcode': (str, ""),
                                   'from_year': (int, 0),
                                   'from_month': (int, 0),
                                   'from_day': (int, 0),
                                   'to_year': (int, 0),
                                   'to_month': (int, 0),
                                   'to_day': (int, 0),
                                   })

        #raise repr(form)

        uid = getUid(req)

        body = perform_new_loan_request_send(recid=self.recid,
                                             uid=uid,
                                             barcode=argd['barcode'],
                                             from_year=argd['from_year'],
                                             from_month=argd['from_month'],
                                             from_day=argd['from_day'],
                                             to_year=argd['to_year'],
                                             to_month=argd['to_month'],
                                             to_day=argd['to_day'],
                                             ln=argd['ln'])


        _ = gettext_set_language(argd['ln'])


        user_info = collect_user_info(req)
        (auth_code, auth_msg) = check_user_can_view_record(user_info, self.recid)
        if auth_code and user_info['email'] == 'guest' and not user_info['apache_user']:
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            target = '/youraccount/login' + \
                     make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : \
                CFG_SITE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target)
        elif auth_code:
            return page_not_authorized(req, "../", \
                text = auth_msg)



        unordered_tabs = get_detailed_page_tabs(get_colID(guess_primary_collection_of_a_record(self.recid)),
                                                    self.recid,
                                                    ln=argd['ln'])
        ordered_tabs_id = [(tab_id, values['order']) for (tab_id, values) in unordered_tabs.iteritems()]
        ordered_tabs_id.sort(lambda x, y: cmp(x[1], y[1]))
        link_ln = ''
        if argd['ln'] != CFG_SITE_LANG:
            link_ln = '?ln=%s' % argd['ln']
        tabs = [(unordered_tabs[tab_id]['label'], \
                 '%s/record/%s/%s%s' % (CFG_SITE_URL, self.recid, tab_id, link_ln), \
                 tab_id in ['holdings'],
                 unordered_tabs[tab_id]['enabled']) \
                for (tab_id, order) in ordered_tabs_id
                if unordered_tabs[tab_id]['visible'] == True]
        top = webstyle_templates.detailed_record_container_top(self.recid,
                                                               tabs,
                                                               argd['ln'])
        bottom = webstyle_templates.detailed_record_container_bottom(self.recid,
                                                                     tabs,
                                                                     argd['ln'])

        title, description, keywords = websearch_templates.tmpl_record_page_header_content(req, self.recid, argd['ln'])
        navtrail = create_navtrail_links(cc=guess_primary_collection_of_a_record(self.recid), ln=argd['ln'])
        navtrail += ' &gt; <a class="navtrail" href="%s/record/%s?ln=%s">'% (CFG_SITE_URL, self.recid, argd['ln'])
        navtrail += title
        navtrail += '</a>'

        return pageheaderonly(title=title,
                              navtrail=navtrail,
                              uid=uid,
                              verbose=1,
                              req=req,
                              language=argd['ln'],
                              navmenuid='search',
                              navtrail_append_title_p=0) + \
                              websearch_templates.tmpl_search_pagestart(argd['ln']) + \
                              top + body + bottom + \
                              websearch_templates.tmpl_search_pageend(argd['ln']) + \
                              pagefooteronly(lastupdated=__lastupdated__,
                                             language=argd['ln'], req=req)



