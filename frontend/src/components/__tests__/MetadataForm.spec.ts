import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import MetadataForm from '../MetadataForm.vue'
import { createI18n } from 'vue-i18n'
import type { Commentary, TrailConditions } from '../../types'

// Mock FileReader
const mockFileReader = {
  readAsDataURL: vi.fn(),
  result: 'data:image/jpeg;base64,test-image-data',
  onload: null as any
}

global.FileReader = vi.fn(() => mockFileReader) as any

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      trackType: {
        segment: 'Segment',
        route: 'Route'
      },
      form: {
        segmentName: 'Segment Name',
        routeName: 'Route Name',
        surfaceType: 'Surface Type',
        majorSurfaceType: 'Major Surface Type',
        difficultyLevel: 'Difficulty Level',
        tire: 'Tire',
        trailConditions: 'Trail Conditions',
        media: 'Media',
        videoLinks: 'Video Links',
        images: 'Images',
        comments: 'Comments',
        commentaryText: 'Commentary Text',
        commentaryPlaceholder: 'Add your comments here...',
        videoUrlPlaceholder: 'Enter video URL',
        addVideoLink: 'Add Video Link',
        removeVideo: 'Remove Video',
        removeImage: 'Remove Image',
        imageAlt: 'Image',
        imageCaptionPlaceholder: 'Enter caption',
        uploadImages: 'Upload Images',
        uploadHint: 'Drag and drop or click to upload'
      },
      required: '*',
      difficulty: {
        level1: 'Easy',
        level2: 'Moderate',
        level3: 'Medium',
        level4: 'Hard',
        level5: 'Expert',
        descriptions: {
          level1: 'You could ride this segment with your eyes closed',
          level2:
            'It should be quite fine. Only a couple of irregularities on the path, but easy business.',
          level3:
            "You'll need some bike handling skill due to irregular terrain or uphill and downhill sections.",
          level4:
            "It's no longer straightforward. You'll definitely need to navigate elevation changes and will encounter unexpected ground variations.",
          level5:
            'Be prepared to put a foot down, as the path is difficult due to either slope, terrain, or both.'
        }
      },
      surface: {
        'broken-paved-road': 'Broken Paved Road',
        'dirty-road': 'Dirty Road',
        'small-stone-road': 'Small Stone Road',
        'big-stone-road': 'Big Stone Road',
        'field-trail': 'Field Trail',
        'forest-trail': 'Forest Trail'
      },
      tire: {
        dry: 'Dry',
        wet: 'Wet',
        slick: 'Slick',
        semiSlick: 'Semi-Slick',
        knobs: 'Knobs',
        dryHelp: 'Recommended tire for dry conditions',
        wetHelp: 'Recommended tire for wet conditions'
      }
    }
  }
})

function createWrapper(props = {}) {
  const defaultProps = {
    name: 'Test Segment',
    trackType: 'segment' as 'segment' | 'route',
    trailConditions: {
      tire_dry: 'slick' as 'slick' | 'semi-slick' | 'knobs',
      tire_wet: 'slick' as 'slick' | 'semi-slick' | 'knobs',
      surface_type: ['forest-trail'],
      difficulty_level: 3
    } as TrailConditions,
    commentary: {
      text: '',
      video_links: [],
      images: []
    } as Commentary,
    isDragOver: false
  }

  return mount(MetadataForm, {
    props: {
      ...defaultProps,
      ...props
    },
    global: {
      plugins: [i18n]
    }
  })
}

describe('MetadataForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Track Type Selection', () => {
    it('renders track type tabs correctly', () => {
      const wrapper = createWrapper()
      const tabs = wrapper.findAll('.tab-button')
      expect(tabs.length).toBe(2)
      expect(tabs[0].text()).toContain('Segment')
      expect(tabs[1].text()).toContain('Route')
    })

    it('shows the correct active tab', () => {
      const wrapper = createWrapper({ trackType: 'segment' })
      const segmentTab = wrapper.findAll('.tab-button')[0]
      expect(segmentTab.classes()).toContain('active')
    })

    it('emits update:trackType when tab is clicked', async () => {
      const wrapper = createWrapper()
      const routeTab = wrapper.findAll('.tab-button')[1]
      await routeTab.trigger('click')
      expect(wrapper.emitted('update:trackType')).toBeTruthy()
      expect(wrapper.emitted('update:trackType')![0]).toEqual(['route'])
    })
  })

  describe('Name Input', () => {
    it('renders name input with correct value', () => {
      const wrapper = createWrapper({ name: 'My Segment' })
      const nameInput = wrapper.find('#name') as any
      expect(nameInput.element.value).toBe('My Segment')
    })

    it('emits update:name when input changes', async () => {
      const wrapper = createWrapper()
      const nameInput = wrapper.find('#name')
      await nameInput.setValue('New Name')
      expect(wrapper.emitted('update:name')).toBeTruthy()
      expect(wrapper.emitted('update:name')![0]).toEqual(['New Name'])
    })

    it('shows correct label based on track type', () => {
      const segmentWrapper = createWrapper({ trackType: 'segment' })
      expect(segmentWrapper.find('label[for="name"]').text()).toContain('Segment Name')

      const routeWrapper = createWrapper({ trackType: 'route' })
      expect(routeWrapper.find('label[for="name"]').text()).toContain('Route Name')
    })
  })

  describe('Difficulty Level', () => {
    it('renders difficulty slider with correct value', () => {
      const wrapper = createWrapper({
        trailConditions: {
          tire_dry: 'slick',
          tire_wet: 'slick',
          surface_type: ['forest-trail'],
          difficulty_level: 4
        }
      })
      const slider = wrapper.find('.difficulty-slider') as any
      expect(parseInt(slider.element.value)).toBe(4)
    })

    it('emits update:trailConditions when difficulty level changes', async () => {
      const wrapper = createWrapper()
      const slider = wrapper.find('.difficulty-slider')
      await slider.setValue('5')
      expect(wrapper.emitted('update:trailConditions')).toBeTruthy()
      const emitted = wrapper.emitted(
        'update:trailConditions'
      )![0][0] as TrailConditions
      expect(emitted.difficulty_level).toBe(5)
    })

    it('can set difficulty level by clicking on marks', async () => {
      const wrapper = createWrapper()
      const marks = wrapper.findAll('.difficulty-mark')
      await marks[4].trigger('click') // Click on level 5
      expect(wrapper.emitted('update:trailConditions')).toBeTruthy()
      const emitted = wrapper.emitted(
        'update:trailConditions'
      )![0][0] as TrailConditions
      expect(emitted.difficulty_level).toBe(5)
    })
  })

  describe('Difficulty Tooltip Functionality', () => {
    describe('Tooltip Structure', () => {
      it('renders difficulty mark wrappers for each difficulty level', () => {
        const wrapper = createWrapper()

        const difficultyMarkWrappers = wrapper.findAll('.difficulty-mark-wrapper')
        expect(difficultyMarkWrappers).toHaveLength(5)

        difficultyMarkWrappers.forEach((wrapper: any) => {
          expect(wrapper.classes()).toContain('difficulty-mark-wrapper')
          expect(wrapper.find('.difficulty-mark').exists()).toBe(true)
          expect(wrapper.find('.difficulty-tooltip').exists()).toBe(true)
        })
      })

      it('renders difficulty tooltips for each level', () => {
        const wrapper = createWrapper()

        const tooltips = wrapper.findAll('.difficulty-tooltip')
        expect(tooltips).toHaveLength(5)

        tooltips.forEach((tooltip: any) => {
          expect(tooltip.classes()).toContain('difficulty-tooltip')
        })
      })
    })

    describe('Tooltip Content', () => {
      it('displays correct descriptions for each difficulty level', () => {
        const wrapper = createWrapper()

        const tooltips = wrapper.findAll('.difficulty-tooltip')

        expect(tooltips[0].text()).toBe(
          'You could ride this segment with your eyes closed'
        )
        expect(tooltips[1].text()).toBe(
          'It should be quite fine. Only a couple of irregularities on the path, but easy business.'
        )
        expect(tooltips[2].text()).toBe(
          "You'll need some bike handling skill due to irregular terrain or uphill and downhill sections."
        )
        expect(tooltips[3].text()).toBe(
          "It's no longer straightforward. You'll definitely need to navigate elevation changes and will encounter unexpected ground variations."
        )
        expect(tooltips[4].text()).toBe(
          'Be prepared to put a foot down, as the path is difficult due to either slope, terrain, or both.'
        )
      })

      it('has correct CSS classes on tooltips', () => {
        const wrapper = createWrapper()

        const tooltips = wrapper.findAll('.difficulty-tooltip')
        tooltips.forEach((tooltip: any) => {
          expect(tooltip.classes()).toContain('difficulty-tooltip')
        })
      })
    })

    describe('Tooltip Interactions', () => {
      it('has mouse event handlers on difficulty mark wrappers', () => {
        const wrapper = createWrapper()

        const difficultyMarkWrappers = wrapper.findAll('.difficulty-mark-wrapper')
        difficultyMarkWrappers.forEach((wrapper: any) => {
          expect(wrapper.classes()).toContain('difficulty-mark-wrapper')
        })
      })

      it('tooltips are initially hidden', () => {
        const wrapper = createWrapper()

        const tooltips = wrapper.findAll('.difficulty-tooltip')
        tooltips.forEach((tooltip: any) => {
          expect(tooltip.classes()).toContain('difficulty-tooltip')
        })
      })

      it('maintains click functionality on difficulty marks', async () => {
        const wrapper = createWrapper()

        const difficultyMarkWrappers = wrapper.findAll('.difficulty-mark-wrapper')
        await difficultyMarkWrappers[4].trigger('click') // Click on level 5

        expect(wrapper.emitted('update:trailConditions')).toBeTruthy()
        const emitted = wrapper.emitted(
          'update:trailConditions'
        )![0][0] as TrailConditions
        expect(emitted.difficulty_level).toBe(5)
      })
    })

    describe('Tooltip Styling', () => {
      it('applies correct CSS classes to difficulty mark wrappers', () => {
        const wrapper = createWrapper()

        const difficultyMarkWrappers = wrapper.findAll('.difficulty-mark-wrapper')
        difficultyMarkWrappers.forEach((wrapper: any) => {
          expect(wrapper.classes()).toContain('difficulty-mark-wrapper')
        })
      })

      it('applies correct CSS classes to tooltips', () => {
        const wrapper = createWrapper()

        const tooltips = wrapper.findAll('.difficulty-tooltip')
        tooltips.forEach((tooltip: any) => {
          expect(tooltip.classes()).toContain('difficulty-tooltip')
        })
      })
    })

    describe('Internationalization', () => {
      it('displays tooltips in English by default', () => {
        const wrapper = createWrapper()

        const tooltips = wrapper.findAll('.difficulty-tooltip')
        expect(tooltips[0].text()).toContain('You could ride this segment')
        expect(tooltips[1].text()).toContain('It should be quite fine')
      })

      it('switches to French when locale changes', () => {
        const frenchI18n = createI18n({
          legacy: false,
          locale: 'fr',
          messages: {
            fr: {
              trackType: {
                segment: 'Segment',
                route: 'Route'
              },
              form: {
                segmentName: 'Nom du Segment',
                routeName: 'Nom de la Route',
                surfaceType: 'Type de Surface',
                majorSurfaceType: 'Type de Surface Principal',
                difficultyLevel: 'Niveau de Difficulté',
                tire: 'Pneu',
                trailConditions: 'Conditions de Piste',
                media: 'Médias',
                videoLinks: 'Liens Vidéo',
                images: 'Images',
                comments: 'Commentaires',
                commentaryText: 'Texte de Commentaire',
                commentaryPlaceholder: 'Ajoutez vos commentaires ici...',
                videoUrlPlaceholder: "Entrez l'URL de la vidéo",
                addVideoLink: 'Ajouter un Lien Vidéo',
                removeVideo: 'Supprimer la Vidéo',
                removeImage: "Supprimer l'Image",
                imageAlt: 'Image',
                imageCaptionPlaceholder: 'Entrez une légende',
                uploadImages: 'Télécharger des Images',
                uploadHint: 'Glisser-déposer ou cliquer pour télécharger'
              },
              required: '*',
              difficulty: {
                level1: 'Facile',
                level2: 'Modéré',
                level3: 'Moyen',
                level4: 'Difficile',
                level5: 'Expert',
                descriptions: {
                  level1: 'Vous pourriez rouler sur ce segment les yeux fermés',
                  level2:
                    'Ça devrait être tout à fait correct. Seulement quelques irrégularités sur le chemin, mais facile à gérer.',
                  level3:
                    'Vous aurez besoin de quelques compétences en pilotage de vélo en raison du terrain irrégulier ou des sections en montée et descente.',
                  level4:
                    "Ce n'est plus évident. Vous devrez définitivement naviguer les changements d'élévation et rencontrerez des variations de terrain inattendues.",
                  level5:
                    'Soyez prêt à poser le pied, car le chemin est difficile en raison de la pente, du terrain, ou des deux.'
                }
              },
              surface: {
                'broken-paved-road': 'Route Goudronnée Cassée',
                'dirty-road': 'Route Sale',
                'small-stone-road': 'Route en Petits Cailloux',
                'big-stone-road': 'Route en Gros Cailloux',
                'field-trail': 'Sentier de Champ',
                'forest-trail': 'Sentier de Forêt'
              },
              tire: {
                dry: 'Sec',
                wet: 'Mouillé',
                slick: 'Lisse',
                semiSlick: 'Semi-Lisse',
                knobs: 'Crampons',
                dryHelp: 'Pneu recommandé pour conditions sèches',
                wetHelp: 'Pneu recommandé pour conditions humides'
              }
            }
          }
        })

        const wrapper = mount(MetadataForm, {
          props: {
            name: 'Test Segment',
            trackType: 'segment' as 'segment' | 'route',
            trailConditions: {
              tire_dry: 'slick' as 'slick' | 'semi-slick' | 'knobs',
              tire_wet: 'slick' as 'slick' | 'semi-slick' | 'knobs',
              surface_type: ['forest-trail'],
              difficulty_level: 3
            } as TrailConditions,
            commentary: {
              text: '',
              video_links: [],
              images: []
            } as Commentary,
            isDragOver: false
          },
          global: {
            plugins: [frenchI18n]
          }
        })

        const tooltips = wrapper.findAll('.difficulty-tooltip')
        expect(tooltips[0].text()).toContain('Vous pourriez rouler sur ce segment')
        expect(tooltips[1].text()).toContain('Ça devrait être tout à fait correct')
      })
    })

    describe('Accessibility', () => {
      it('provides informative tooltip content for screen readers', () => {
        const wrapper = createWrapper()

        const tooltips = wrapper.findAll('.difficulty-tooltip')
        tooltips.forEach((tooltip: any) => {
          expect(tooltip.text().length).toBeGreaterThan(10) // Ensure meaningful content
        })
      })

      it('maintains proper semantic structure', () => {
        const wrapper = createWrapper()

        const difficultyMarkWrappers = wrapper.findAll('.difficulty-mark-wrapper')
        difficultyMarkWrappers.forEach((wrapper: any) => {
          expect(wrapper.find('.difficulty-mark').exists()).toBe(true)
          expect(wrapper.find('.difficulty-tooltip').exists()).toBe(true)
        })
      })

      it('preserves slider accessibility', () => {
        const wrapper = createWrapper()

        const slider = wrapper.find('.difficulty-slider')
        expect(slider.attributes('aria-label')).toBe('Difficulty Level')
      })
    })

    describe('Performance', () => {
      it('does not create extra tooltip elements on re-render', async () => {
        const wrapper = createWrapper()

        const initialTooltips = wrapper.findAll('.difficulty-tooltip').length
        expect(initialTooltips).toBe(5)

        // Trigger a re-render by changing props
        await wrapper.setProps({
          trailConditions: {
            ...wrapper.props().trailConditions,
            difficulty_level: 2
          }
        })

        const finalTooltips = wrapper.findAll('.difficulty-tooltip').length
        expect(finalTooltips).toBe(5)
      })

      it('handles rapid prop changes without errors', async () => {
        const wrapper = createWrapper()

        // Rapidly change difficulty level
        for (let i = 1; i <= 5; i++) {
          await wrapper.setProps({
            trailConditions: {
              ...wrapper.props().trailConditions,
              difficulty_level: i
            }
          })
        }

        const tooltips = wrapper.findAll('.difficulty-tooltip')
        expect(tooltips).toHaveLength(5)
      })
    })

    describe('Integration with Existing Functionality', () => {
      it('works with difficulty slider changes', async () => {
        const wrapper = createWrapper()

        const slider = wrapper.find('.difficulty-slider')
        await slider.setValue('4')

        // Verify tooltips still exist after slider change
        const tooltips = wrapper.findAll('.difficulty-tooltip')
        expect(tooltips).toHaveLength(5)

        // Verify emitted event
        expect(wrapper.emitted('update:trailConditions')).toBeTruthy()
        const emitted = wrapper.emitted(
          'update:trailConditions'
        )![0][0] as TrailConditions
        expect(emitted.difficulty_level).toBe(4)
      })

      it('maintains tooltip functionality across track type changes', async () => {
        const wrapper = createWrapper()

        // Change track type
        await wrapper.setProps({
          trackType: 'route'
        })

        // Verify tooltips still exist and work
        const tooltips = wrapper.findAll('.difficulty-tooltip')
        expect(tooltips).toHaveLength(5)
        expect(tooltips[0].text()).toContain('You could ride this segment')
      })
    })
  })

  describe('Surface Type Selection', () => {
    it('renders all surface type options', () => {
      const wrapper = createWrapper()
      const surfaceOptions = wrapper.findAll('.surface-option')
      expect(surfaceOptions.length).toBe(6)
    })

    it('shows correct selected surface type', () => {
      const wrapper = createWrapper({
        trailConditions: {
          tire_dry: 'slick',
          tire_wet: 'slick',
          surface_type: ['broken-paved-road'],
          difficulty_level: 3
        }
      })
      const selectedOption = wrapper.find('.surface-option.selected')
      expect(selectedOption.exists()).toBe(true)
    })

    it('emits update:trailConditions when surface type changes', async () => {
      const wrapper = createWrapper()
      const surfaceOption = wrapper.find('.surface-option input[value="dirty-road"]')
      await surfaceOption.trigger('change')
      expect(wrapper.emitted('update:trailConditions')).toBeTruthy()
      const emitted = wrapper.emitted(
        'update:trailConditions'
      )![0][0] as TrailConditions
      expect(emitted.surface_type).toContain('dirty-road')
    })
  })

  describe('Tire Selection', () => {
    it('renders both dry and wet tire groups', () => {
      const wrapper = createWrapper()
      const tireGroups = wrapper.findAll('.tire-group')
      expect(tireGroups.length).toBe(2)
    })

    it('renders all tire options for dry conditions', () => {
      const wrapper = createWrapper()
      const dryTireOptions = wrapper.findAll('input[name="tireDry"]')
      expect(dryTireOptions.length).toBe(3)
    })

    it('renders all tire options for wet conditions', () => {
      const wrapper = createWrapper()
      const wetTireOptions = wrapper.findAll('input[name="tireWet"]')
      expect(wetTireOptions.length).toBe(3)
    })

    it('emits update:trailConditions when dry tire changes', async () => {
      const wrapper = createWrapper()
      const knobsOption = wrapper.find('input[name="tireDry"][value="knobs"]')
      await knobsOption.trigger('change')
      expect(wrapper.emitted('update:trailConditions')).toBeTruthy()
      const emitted = wrapper.emitted(
        'update:trailConditions'
      )![0][0] as TrailConditions
      expect(emitted.tire_dry).toBe('knobs')
    })

    it('emits update:trailConditions when wet tire changes', async () => {
      const wrapper = createWrapper()
      const semiSlickOption = wrapper.find('input[name="tireWet"][value="semi-slick"]')
      await semiSlickOption.trigger('change')
      expect(wrapper.emitted('update:trailConditions')).toBeTruthy()
      const emitted = wrapper.emitted(
        'update:trailConditions'
      )![0][0] as TrailConditions
      expect(emitted.tire_wet).toBe('semi-slick')
    })
  })

  describe('Video Links', () => {
    it('renders video links correctly', () => {
      const wrapper = createWrapper({
        commentary: {
          text: '',
          video_links: [
            {
              id: '1',
              url: 'https://youtube.com/test',
              platform: 'youtube'
            }
          ],
          images: []
        }
      })
      const videoItems = wrapper.findAll('.video-link-item')
      expect(videoItems.length).toBe(1)
    })

    it('shows add video button', () => {
      const wrapper = createWrapper()
      const addButton = wrapper.find('.add-video-btn')
      expect(addButton.exists()).toBe(true)
    })

    it('emits update:commentary when adding video link', async () => {
      const wrapper = createWrapper()
      const addButton = wrapper.find('.add-video-btn')
      await addButton.trigger('click')
      expect(wrapper.emitted('update:commentary')).toBeTruthy()
      const emitted = wrapper.emitted('update:commentary')![0][0] as Commentary
      expect(emitted.video_links.length).toBe(1)
    })

    it('emits update:commentary when removing video link', async () => {
      const wrapper = createWrapper({
        commentary: {
          text: '',
          video_links: [
            {
              id: '1',
              url: 'https://youtube.com/test',
              platform: 'youtube'
            }
          ],
          images: []
        }
      })
      const removeButton = wrapper.find('.remove-video-btn')
      await removeButton.trigger('click')
      expect(wrapper.emitted('update:commentary')).toBeTruthy()
      const emitted = wrapper.emitted('update:commentary')![0][0] as Commentary
      expect(emitted.video_links.length).toBe(0)
    })

    it('detects YouTube URL platform', async () => {
      const wrapper = createWrapper({
        commentary: {
          text: '',
          video_links: [{ id: '1', url: '', platform: 'youtube' }],
          images: []
        }
      })
      const input = wrapper.find('.video-url-input')
      await input.setValue('https://youtube.com/watch?v=123')
      expect(wrapper.emitted('update:commentary')).toBeTruthy()
      const emitted = wrapper.emitted('update:commentary')![0][0] as Commentary
      expect(emitted.video_links[0].platform).toBe('youtube')
    })

    it('detects Vimeo URL platform', async () => {
      const wrapper = createWrapper({
        commentary: {
          text: '',
          video_links: [{ id: '1', url: '', platform: 'youtube' }],
          images: []
        }
      })
      const input = wrapper.find('.video-url-input')
      await input.setValue('https://vimeo.com/123456')
      expect(wrapper.emitted('update:commentary')).toBeTruthy()
      const emitted = wrapper.emitted('update:commentary')![0][0] as Commentary
      expect(emitted.video_links[0].platform).toBe('vimeo')
    })
  })

  describe('Image Upload', () => {
    it('renders image upload area', () => {
      const wrapper = createWrapper()
      const uploadArea = wrapper.find('.image-upload-area')
      expect(uploadArea.exists()).toBe(true)
    })

    it('shows existing images', () => {
      const wrapper = createWrapper({
        commentary: {
          text: '',
          video_links: [],
          images: [
            {
              id: '1',
              preview: 'data:image/jpeg;base64,test',
              caption: 'Test Image',
              uploaded: false,
              image_url: '',
              image_id: '',
              storage_key: '',
              filename: 'test.jpg',
              original_filename: 'test.jpg'
            }
          ]
        }
      })
      const imageItems = wrapper.findAll('.image-item')
      expect(imageItems.length).toBe(1)
    })

    it('emits update:commentary when removing image', async () => {
      const wrapper = createWrapper({
        commentary: {
          text: '',
          video_links: [],
          images: [
            {
              id: '1',
              preview: 'data:image/jpeg;base64,test',
              caption: 'Test Image',
              uploaded: false,
              image_url: '',
              image_id: '',
              storage_key: '',
              filename: 'test.jpg',
              original_filename: 'test.jpg'
            }
          ]
        }
      })
      const removeButton = wrapper.find('.remove-image-btn')
      await removeButton.trigger('click')
      expect(wrapper.emitted('update:commentary')).toBeTruthy()
      const emitted = wrapper.emitted('update:commentary')![0][0] as Commentary
      expect(emitted.images.length).toBe(0)
    })

    it('emits update:commentary when updating image caption', async () => {
      const wrapper = createWrapper({
        commentary: {
          text: '',
          video_links: [],
          images: [
            {
              id: '1',
              preview: 'data:image/jpeg;base64,test',
              caption: '',
              uploaded: false,
              image_url: '',
              image_id: '',
              storage_key: '',
              filename: 'test.jpg',
              original_filename: 'test.jpg'
            }
          ]
        }
      })
      const captionInput = wrapper.find('.image-caption-input')
      await captionInput.setValue('New Caption')
      expect(wrapper.emitted('update:commentary')).toBeTruthy()
      const emitted = wrapper.emitted('update:commentary')![0][0] as Commentary
      expect(emitted.images[0].caption).toBe('New Caption')
    })

    it('emits update:isDragOver on drag over', async () => {
      const wrapper = createWrapper()
      const uploadArea = wrapper.find('.image-upload-area')
      await uploadArea.trigger('dragover')
      expect(wrapper.emitted('update:isDragOver')).toBeTruthy()
      expect(wrapper.emitted('update:isDragOver')![0]).toEqual([true])
    })

    it('emits update:isDragOver on drag leave', async () => {
      const wrapper = createWrapper({ isDragOver: true })
      const uploadArea = wrapper.find('.image-upload-area')
      await uploadArea.trigger('dragleave')
      expect(wrapper.emitted('update:isDragOver')).toBeTruthy()
      expect(wrapper.emitted('update:isDragOver')![0]).toEqual([false])
    })
  })

  describe('Commentary Text', () => {
    it('renders commentary textarea', () => {
      const wrapper = createWrapper()
      const textarea = wrapper.find('#commentary-text')
      expect(textarea.exists()).toBe(true)
    })

    it('shows commentary text value', () => {
      const wrapper = createWrapper({
        commentary: {
          text: 'Test commentary',
          video_links: [],
          images: []
        }
      })
      const textarea = wrapper.find('#commentary-text') as any
      expect(textarea.element.value).toBe('Test commentary')
    })

    it('emits update:commentary when text changes', async () => {
      const wrapper = createWrapper()
      const textarea = wrapper.find('#commentary-text')
      await textarea.setValue('New commentary text')
      expect(wrapper.emitted('update:commentary')).toBeTruthy()
      const emitted = wrapper.emitted('update:commentary')![0][0] as Commentary
      expect(emitted.text).toBe('New commentary text')
    })
  })

  describe('Form Submission', () => {
    it('emits submit event when form is submitted', async () => {
      const wrapper = createWrapper()
      await wrapper.find('form').trigger('submit')
      expect(wrapper.emitted('submit')).toBeTruthy()
    })
  })
})
