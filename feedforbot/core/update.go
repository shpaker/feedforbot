package core

import (
	"fmt"
	"net/url"
	"time"

	pongo2 "github.com/flosch/pongo2/v6"
)

type Author struct {
	Name  string
	Email *string
	Url   *url.URL
}

func (a Author) String() string {
	if a.Email != nil {
		return fmt.Sprintf("%s <%s>", a.Name, *a.Email)
	}
	return a.Name
}

type Update struct {
	Id          string
	PublishedAt time.Time
	ReceivedAt  time.Time
	Url         url.URL
	Title       string
	Text        string
	Images      []url.URL
	Authors     []Author
	Categories  []string
}

func (t *Update) GetTemplateContext() pongo2.Context {
	return pongo2.Context{
		"id":           t.Id,
		"published_at": t.PublishedAt,
		"received_at":  t.ReceivedAt,
		"url":          t.Url,
		"title":        t.Title,
		"text":         t.Text,
		"images":       t.Images,
		"authors":      t.Authors,
		"categories":   t.Categories,
	}
}
