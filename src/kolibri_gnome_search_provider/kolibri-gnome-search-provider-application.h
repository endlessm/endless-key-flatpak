/* kolibri-gnome-search-provider-application.h
 *
 * Copyright 2021 Endless OS Foundation
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE X CONSORTIUM BE LIABLE FOR ANY
 * CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
 * TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 * SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 *
 * Except as contained in this notice, the name(s) of the above copyright
 * holders shall not be used in advertising or otherwise to promote the sale,
 * use or other dealings in this Software without prior written
 * authorization.
 *
 * SPDX-License-Identifier: MIT
 *
 * Author: Dylan McCall <dylan@endlessos.org>
 */

#ifndef KOLIBRI_GNOME_SEARCH_PROVIDER_APPLICATION_H
#define KOLIBRI_GNOME_SEARCH_PROVIDER_APPLICATION_H

#include <glib-object.h>
#include <gio/gio.h>

G_BEGIN_DECLS

#define KOLIBRI_GNOME_TYPE_SEARCH_PROVIDER_APPLICATION kolibri_gnome_search_provider_application_get_type()
G_DECLARE_FINAL_TYPE(KolibriGnomeSearchProviderApplication, kolibri_gnome_search_provider_application, KOLIBRI_GNOME, SEARCH_PROVIDER_APPLICATION, GApplication)

KolibriGnomeSearchProviderApplication *kolibri_gnome_search_provider_application_new(const gchar * application_id, GApplicationFlags flags);

void kolibri_gnome_search_provider_application_reset_inactivity_timeout(KolibriGnomeSearchProviderApplication *self);

G_END_DECLS

#endif
