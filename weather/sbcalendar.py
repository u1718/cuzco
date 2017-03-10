from calendar import HTMLCalendar, monthrange
from datetime import timedelta
from django.core.urlresolvers import reverse

class SideBarCalendar(HTMLCalendar):
    def __init__(self, viewname, selecteday):
        super(SideBarCalendar, self).__init__()
        self.viewname = viewname
        self.selday = selecteday
        self.smonth = selecteday.month
        self.syear = selecteday.year

    def formatmonth(self):
        nextmonth = self.selday + timedelta(days=monthrange(self.syear, self.smonth)[1])
        prevmonth = self.selday + timedelta(days=-self.selday.day)
        prevlink =  'Prev: <a href="%s">%s</a>' % \
                    (reverse(self.viewname, args=(prevmonth.year, prevmonth.month, 1)),
                     prevmonth.strftime('%h %Y'))
        nextlink =  'Next: <a href="%s">%s</a>' % \
                    (reverse(self.viewname, args=(nextmonth.year, nextmonth.month, 1)),
                     nextmonth.strftime('%h %Y'))
        return '<div class="row"><div class="col-md-3"></div>'\
                                '<div class="col-md-4"><br><br>%s<br>%s</div>' \
                                '<div class="col-md-5">%s<br></div></div>' % \
          (prevlink, nextlink, \
           super(SideBarCalendar, self).formatmonth(self.syear, self.smonth, withyear=True))

    def formatday(self, day, weekday):
        if day == 0:
            return self.day_cell('noday', '&nbsp;')

        cssclass = self.cssclasses[weekday]
        if self.selday.day == day:
            cssclass += ' today'

        return self.day_cell(cssclass,
                             '<a href="%s">%d</a>' % \
                             (reverse(self.viewname, args=(self.syear, self.smonth, day)),
                              day))

    def day_cell(self, cssclass, body):
        return '<td class="%s">%s</td>' % (cssclass, body)

    def formatweekday(self, day):
        """
        Return a weekday name as a table header.
        """
        cssclasses = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        day_abbr = ["mo", "tu", "we", "th", "fr", "sa", "su"]
        return '<th class="%s">%s</th>' % (cssclasses[day], day_abbr[day])

