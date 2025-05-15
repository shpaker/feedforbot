package core

import (
	"net/url"
	"time"

	"github.com/mmcdole/gofeed"
)

type Source interface {
	GetUpdates() []Update
}

// type Transport interface {
// 	Send([]Update) []Update
// }

type FeedSource struct {
	Url url.URL
}

func (s FeedSource) convertAuthors(persons []*gofeed.Person) []Author {
	var authors []Author
	for _, person := range persons {
		author := Author{
			Name: person.Name,
		}
		if person.Email != "" {
			email := person.Email
			author.Email = &email
		}
		authors = append(authors, author)
	}
	return authors
}

func (s FeedSource) makeUpdate(item *gofeed.Item) Update {
	pubDate := item.PublishedParsed
	if pubDate == nil {
		pubDate = item.UpdatedParsed
	}
	if pubDate == nil {
		return Update{}
	}

	rawLink := item.Link
	if rawLink == "" {
		rawLink = item.GUID
	}
	itemUrl, err := url.Parse(rawLink)
	if err != nil {
		return Update{}
	}

	var images []url.URL
	if item.Image != nil {
		if imgUrl, err := url.Parse(item.Image.URL); err == nil {
			images = append(images, *imgUrl)
		}
	}

	id := item.GUID
	if id == "" {
		id = itemUrl.String()
	}

	return Update{
		Id:          id,
		PublishedAt: *pubDate,
		ReceivedAt:  time.Now(),
		Url:         *itemUrl,
		Title:       item.Title,
		Text:        item.Description,
		Images:      images,
		Authors:     s.convertAuthors(item.Authors),
		Categories:  item.Categories,
	}
}

func (s FeedSource) GetUpdates() []Update {
	fp := gofeed.NewParser()
	feed, err := fp.ParseURL(s.Url.String())

	if err != nil {
		return nil
	}

	var articles []Update

	for _, item := range feed.Items {
		article := s.makeUpdate(item)
		articles = append(articles, article)
	}

	return articles
}
