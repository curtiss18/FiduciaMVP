  const fetchContentData = async () => {
    try {
      setIsLoading(true)
      
      // Fetch content list
      const contentResponse = await contentApi.getContent()
      console.log('Content response:', contentResponse.data)
      setContent(contentResponse.data.content || [])
      
      // Fetch statistics  
      const statsResponse = await contentApi.getContentStatistics()
      console.log('Stats response:', statsResponse.data)
      setStats(statsResponse.data.statistics || statsResponse.data)
      
      setLastUpdated(new Date())
      
    } catch (error) {
      console.error('Error fetching content data:', error)
    } finally {
      setIsLoading(false)
    }
  }