import { ParkData, AlertData, VisitorCenterData, CampgroundData, EventData } from './utils/npsApiClient.js';

/**
 * Format the park data into a more readable format for LLMs
 */
export function formatParkData(parkData: ParkData[]) {
  return parkData.map(park => ({
    name: park.fullName,
    code: park.parkCode,
    description: park.description,
    states: park.states.split(',').map(code => code.trim()),
    url: park.url,
    designation: park.designation,
    activities: park.activities.map(activity => activity.name),
    weatherInfo: park.weatherInfo,
    location: {
      latitude: park.latitude,
      longitude: park.longitude
    },
    entranceFees: park.entranceFees.map(fee => ({
      cost: fee.cost,
      description: fee.description,
      title: fee.title
    })),
    operatingHours: park.operatingHours.map(hours => ({
      name: hours.name,
      description: hours.description,
      standardHours: hours.standardHours
    })),
    contacts: {
      phoneNumbers: park.contacts.phoneNumbers.map(phone => ({
        type: phone.type,
        number: phone.phoneNumber,
        description: phone.description
      })),
      emailAddresses: park.contacts.emailAddresses.map(email => ({
        address: email.emailAddress,
        description: email.description
      }))
    },
    images: park.images.map(image => ({
      url: image.url,
      title: image.title,
      altText: image.altText,
      caption: image.caption,
      credit: image.credit
    }))
  }));
}

/**
 * Format park details for a single park
 */
export function formatParkDetails(park: ParkData) {
  // Determine the best address to use as the primary address
  const physicalAddress = park.addresses.find(addr => addr.type === 'Physical') || park.addresses[0];
  
  // Format operating hours in a more readable way
  const formattedHours = park.operatingHours.map(hours => {
    const { standardHours } = hours;
    const formattedStandardHours = Object.entries(standardHours)
      .map(([day, hours]) => {
        // Convert day to proper case (e.g., 'monday' to 'Monday')
        const properDay = day.charAt(0).toUpperCase() + day.slice(1);
        return `${properDay}: ${hours || 'Closed'}`;
      });
      
    return {
      name: hours.name,
      description: hours.description,
      standardHours: formattedStandardHours
    };
  });

  return {
    name: park.fullName,
    code: park.parkCode,
    url: park.url,
    description: park.description,
    designation: park.designation,
    states: park.states.split(',').map(code => code.trim()),
    weatherInfo: park.weatherInfo,
    directionsInfo: park.directionsInfo,
    directionsUrl: park.directionsUrl,
    location: {
      latitude: park.latitude,
      longitude: park.longitude,
      address: physicalAddress ? {
        line1: physicalAddress.line1,
        line2: physicalAddress.line2,
        city: physicalAddress.city,
        stateCode: physicalAddress.stateCode,
        postalCode: physicalAddress.postalCode
      } : undefined
    },
    contacts: {
      phoneNumbers: park.contacts.phoneNumbers.map(phone => ({
        type: phone.type,
        number: phone.phoneNumber,
        extension: phone.extension,
        description: phone.description
      })),
      emailAddresses: park.contacts.emailAddresses.map(email => ({
        address: email.emailAddress,
        description: email.description
      }))
    },
    entranceFees: park.entranceFees.map(fee => ({
      title: fee.title,
      cost: `$${fee.cost}`,
      description: fee.description
    })),
    entrancePasses: park.entrancePasses.map(pass => ({
      title: pass.title,
      cost: `$${pass.cost}`,
      description: pass.description
    })),
    operatingHours: formattedHours,
    topics: park.topics.map(topic => topic.name),
    activities: park.activities.map(activity => activity.name),
    images: park.images.map(image => ({
      url: image.url,
      title: image.title,
      altText: image.altText,
      caption: image.caption,
      credit: image.credit
    }))
  };
}

/**
 * Format the alert data into a more readable format for LLMs
 */
export function formatAlertData(alertData: AlertData[]) {
  return alertData.map(alert => {
    // Get the date part from the lastIndexedDate (which is in ISO format)
    const lastUpdated = alert.lastIndexedDate ? new Date(alert.lastIndexedDate).toLocaleDateString() : 'Unknown';
    
    // Categorize the alert type
    let alertType = alert.category;
    if (alertType === 'Information') {
      alertType = 'Information (non-emergency)';
    } else if (alertType === 'Caution') {
      alertType = 'Caution (potential hazard)';
    } else if (alertType === 'Danger') {
      alertType = 'Danger (significant hazard)';
    } else if (alertType === 'Park Closure') {
      alertType = 'Park Closure (area inaccessible)';
    }
    
    return {
      title: alert.title,
      description: alert.description,
      parkCode: alert.parkCode,
      type: alertType,
      url: alert.url,
      lastUpdated
    };
  });
}

/**
 * Format visitor center data for better readability
 */
export function formatVisitorCenterData(visitorCenterData: VisitorCenterData[]) {
  return visitorCenterData.map(center => {
    // Find physical address if available
    const physicalAddress = center.addresses.find(addr => addr.type === 'Physical') || center.addresses[0];
    
    // Format operating hours
    const formattedHours = center.operatingHours.map(hours => {
      const { standardHours } = hours;
      const formattedStandardHours = Object.entries(standardHours)
        .map(([day, hours]) => {
          // Convert day to proper case (e.g., 'monday' to 'Monday')
          const properDay = day.charAt(0).toUpperCase() + day.slice(1);
          return `${properDay}: ${hours || 'Closed'}`;
        });
        
      return {
        name: hours.name,
        description: hours.description,
        standardHours: formattedStandardHours
      };
    });

    return {
      name: center.name,
      parkCode: center.parkCode,
      description: center.description,
      url: center.url,
      directionsInfo: center.directionsInfo,
      directionsUrl: center.directionsUrl,
      location: {
        latitude: center.latitude,
        longitude: center.longitude,
        address: physicalAddress ? {
          line1: physicalAddress.line1,
          line2: physicalAddress.line2,
          city: physicalAddress.city,
          stateCode: physicalAddress.stateCode,
          postalCode: physicalAddress.postalCode
        } : undefined
      },
      operatingHours: formattedHours,
      contacts: {
        phoneNumbers: center.contacts.phoneNumbers.map(phone => ({
          type: phone.type,
          number: phone.phoneNumber,
          extension: phone.extension,
          description: phone.description
        })),
        emailAddresses: center.contacts.emailAddresses.map(email => ({
          address: email.emailAddress,
          description: email.description
        }))
      }
    };
  });
}

/**
 * Format campground data for better readability
 */
export function formatCampgroundData(campgroundData: CampgroundData[]) {
  return campgroundData.map(campground => {
    // Find physical address if available
    const physicalAddress = campground.addresses.find(addr => addr.type === 'Physical') || campground.addresses[0];
    
    // Format operating hours
    const formattedHours = campground.operatingHours.map(hours => {
      const { standardHours } = hours;
      const formattedStandardHours = Object.entries(standardHours)
        .map(([day, hours]) => {
          const properDay = day.charAt(0).toUpperCase() + day.slice(1);
          return `${properDay}: ${hours || 'Closed'}`;
        });
        
      return {
        name: hours.name,
        description: hours.description,
        standardHours: formattedStandardHours
      };
    });

    // Format amenities for better readability
    const amenities = [];
    if (campground.amenities) {
      if (campground.amenities.trashRecyclingCollection) amenities.push('Trash/Recycling Collection');
      if (campground.amenities.toilets && campground.amenities.toilets.length > 0) 
        amenities.push(`Toilets (${campground.amenities.toilets.join(', ')})`);
      if (campground.amenities.internetConnectivity) amenities.push('Internet Connectivity');
      if (campground.amenities.showers && campground.amenities.showers.length > 0) 
        amenities.push(`Showers (${campground.amenities.showers.join(', ')})`);
      if (campground.amenities.cellPhoneReception) amenities.push('Cell Phone Reception');
      if (campground.amenities.laundry) amenities.push('Laundry');
      if (campground.amenities.amphitheater) amenities.push('Amphitheater');
      if (campground.amenities.dumpStation) amenities.push('Dump Station');
      if (campground.amenities.campStore) amenities.push('Camp Store');
      if (campground.amenities.staffOrVolunteerHostOnsite) amenities.push('Staff/Volunteer Host Onsite');
      if (campground.amenities.potableWater && campground.amenities.potableWater.length > 0) 
        amenities.push(`Potable Water (${campground.amenities.potableWater.join(', ')})`);
      if (campground.amenities.iceAvailableForSale) amenities.push('Ice Available For Sale');
      if (campground.amenities.firewoodForSale) amenities.push('Firewood For Sale');
      if (campground.amenities.foodStorageLockers) amenities.push('Food Storage Lockers');
    }

    return {
      name: campground.name,
      parkCode: campground.parkCode,
      description: campground.description,
      url: campground.url,
      reservationInfo: campground.reservationInfo,
      reservationUrl: campground.reservationUrl,
      regulations: campground.regulationsOverview,
      regulationsUrl: campground.regulationsurl,
      weatherOverview: campground.weatherOverview,
      location: {
        latitude: campground.latitude,
        longitude: campground.longitude,
        address: physicalAddress ? {
          line1: physicalAddress.line1,
          line2: physicalAddress.line2,
          city: physicalAddress.city,
          stateCode: physicalAddress.stateCode,
          postalCode: physicalAddress.postalCode
        } : undefined
      },
      operatingHours: formattedHours,
      fees: campground.fees.map(fee => ({
        title: fee.title,
        cost: `$${fee.cost}`,
        description: fee.description
      })),
      totalSites: campground.campsites?.totalSites || '0',
      sitesReservable: campground.numberOfSitesReservable || '0',
      sitesFirstComeFirstServe: campground.numberOfSitesFirstComeFirstServe || '0',
      campsiteTypes: {
        group: campground.campsites?.group || '0',
        horse: campground.campsites?.horse || '0',
        tentOnly: campground.campsites?.tentOnly || '0',
        electricalHookups: campground.campsites?.electricalHookups || '0',
        rvOnly: campground.campsites?.rvOnly || '0',
        walkBoatTo: campground.campsites?.walkBoatTo || '0',
        other: campground.campsites?.other || '0'
      },
      amenities: amenities,
      accessibility: {
        wheelchairAccess: campground.accessibility?.wheelchairAccess,
        rvAllowed: campground.accessibility?.rvAllowed,
        rvMaxLength: campground.accessibility?.rvMaxLength,
        trailerAllowed: campground.accessibility?.trailerAllowed,
        trailerMaxLength: campground.accessibility?.trailerMaxLength,
        accessRoads: campground.accessibility?.accessRoads,
        adaInfo: campground.accessibility?.adaInfo
      },
      contacts: {
        phoneNumbers: campground.contacts.phoneNumbers.map(phone => ({
          type: phone.type,
          number: phone.phoneNumber,
          extension: phone.extension,
          description: phone.description
        })),
        emailAddresses: campground.contacts.emailAddresses.map(email => ({
          address: email.emailAddress,
          description: email.description
        }))
      }
    };
  });
}

/**
 * Format event data for better readability
 */
export function formatEventData(eventData: EventData[]) {
  return eventData.map(event => {
    // Format dates and times
    const formattedDates = event.dates ? event.dates.join(', ') : '';
    
    // Format times
    const formattedTimes = event.times.map(time => {
      let timeString = '';
      if (time.timeStart) {
        timeString += time.sunriseTimeStart ? 'Sunrise' : time.timeStart;
      }
      if (time.timeEnd) {
        timeString += ' to ';
        timeString += time.sunsetTimeEnd ? 'Sunset' : time.timeEnd;
      }
      return timeString || 'All day';
    }).join(', ');

    return {
      title: event.title,
      parkCode: event.parkCode,
      parkName: event.parkFullName,
      description: event.description,
      category: event.category,
      subcategory: event.subcategory,
      tags: event.tags,
      location: event.location,
      coordinates: {
        latitude: event.latitude,
        longitude: event.longitude
      },
      dateTime: {
        dates: formattedDates,
        times: formattedTimes,
        dateStart: event.dateStart,
        dateEnd: event.dateEnd,
        isAllDay: event.isAllDay,
        isRecurring: event.isRecurring,
        recurrenceDateStart: event.recurrenceDateStart,
        recurrenceDateEnd: event.recurrenceDateEnd
      },
      feeInfo: event.feeInfo,
      contactInfo: {
        email: event.contactEmailAddress,
        phone: event.contactTelephoneNumber
      },
      infoUrl: event.infoURL || event.url,
      lastUpdated: event.lastUpdated
    };
  });
} 