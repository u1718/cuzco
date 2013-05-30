from calendar import HTMLCalendar, monthrange
from datetime import timedelta
from django.core.urlresolvers import reverse

class SbCalendar(HTMLCalendar):
    def __init__(self, viewname, selecteday):
        super(SbCalendar, self).__init__()
        self.viewname = viewname
        self.selday = selecteday
        self.smonth = selecteday.month
        self.syear = selecteday.year

    def formatmonth(self):
        nextmonth = self.selday + timedelta(days=monthrange(self.syear, self.smonth)[1])
        prevmonth = self.selday + timedelta(days=-self.selday.day)
        prevlink =  '<a href="%s">Prev: %s</a>' % \
                    (reverse(self.viewname, args=(prevmonth.year, prevmonth.month, 1)),
                     prevmonth.strftime('%h %Y'))
        nextlink =  '<a href="%s">Next: %s</a>' % \
                    (reverse(self.viewname, args=(nextmonth.year, nextmonth.month, 1)),
                     nextmonth.strftime('%h %Y'))
        return '%s <br>%s <br>%s' % (super(SbCalendar, self).formatmonth(self.syear, self.smonth, withyear=True),
                                     prevlink, nextlink)
        
    def formatday(self, day, weekday):
        if day == 0:
            return self.day_cell('noday', '&nbsp;')

        cssclass = self.cssclasses[weekday]
        if self.selday.day == day:
            cssclass += ' today'

        return self.day_cell(cssclass,
                             '<a href="%s">%d</a>' %
                             (reverse(self.viewname, args=(self.syear, self.smonth, day)),
                              day))

    def day_cell(self, cssclass, body):
        return '<td class="%s">%s</td>' % (cssclass, body)
